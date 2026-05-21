# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import csv
import time
from pathlib import Path

import cv2
import matplotlib.pyplot as plt
import numpy as np
import torch
from ultralytics import YOLO

from drone_detection_yolov8x import (
    _DEFAULT_VIDEO,
    cv2_highgui_available,
    expand_boxes_bottom,
    expand_boxes_left,
    expand_boxes_right,
    shift_boxes_up,
    raise_boxes_bottom,
    maybe_refine_or_suppress_fp,
    smooth_primary_box_xyxy,
)


def _maybe_show_save_close(fig, save_path: str | None, show: bool) -> None:
    if save_path:
        p = Path(save_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(str(p), dpi=160, bbox_inches="tight")
        print("[saved]", p.resolve())
    if show:
        plt.show(block=True)
    plt.close(fig)


def compute_pred_vs_real_errors(
    pred_xy: np.ndarray,
    meas_second: list[tuple[float, float] | None],
    k_pred_start: int,
) -> tuple[dict, list[list]]:
    
    errs: list[float] = []
    rows: list[list] = []
    n = min(len(pred_xy), len(meas_second))
    for j in range(n):
        m = meas_second[j]
        if m is None:
            continue
        p = pred_xy[j]
        rx, ry = float(m[0]), float(m[1])
        px, py = float(p[0]), float(p[1])
        dx, dy = px - rx, py - ry
        e = float(np.hypot(dx, dy))
        kf = int(k_pred_start + j)
        errs.append(e)
        rows.append([kf, e, px, py, rx, ry, dx, dy])
    if not errs:
        return {"n_valid": 0, "n_frames_compared": n, "rmse": None, "mae": None, "max": None, "median": None}, rows
    a = np.asarray(errs, dtype=np.float64)
    return {
        "n_valid": len(errs),
        "n_frames_compared": n,
        "rmse": float(np.sqrt(np.mean(a * a))),
        "mae": float(np.mean(a)),
        "max": float(np.max(a)),
        "median": float(np.median(a)),
    }, rows


def write_error_csv(csv_path: Path, rows: list[list]) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["frame_k", "error_px", "pred_x", "pred_y", "real_x", "real_y", "dx", "dy"])
        w.writerows(rows)


def plot_prediction_error_figure(
    k_arr: np.ndarray,
    err_arr: np.ndarray,
    stats: dict,
    save_path: str | None,
    show: bool,
) -> None:
    fig, ax = plt.subplots(figsize=(8, 4.2))
    if len(err_arr) == 0:
        ax.text(
            0.5,
            0.5,
            ha="center",
            va="center",
            transform=ax.transAxes,
            fontsize=11,
        )
        ax.set_axis_off()
    else:
        ax.plot(k_arr, err_arr, "-", color="tab:red", linewidth=1.2, label="|pred - real|")
        ax.axhline(float(stats["mae"]), color="gray", linestyle="--", linewidth=1, label=f"MAE = {stats['mae']:.2f} px")
        ax.set_xlabel("k — індекс кадру")
        ax.set_ylabel("Похибка, px")
        ax.set_title(
            f"Прогноз і реальність: n={stats['n_valid']}, "
            f"RMSE={stats['rmse']:.2f}, max={stats['max']:.2f} px",
            fontsize=10,
        )
        ax.grid(True, alpha=0.3)
        ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    _maybe_show_save_close(fig, save_path, show)


def write_error_summary_txt(path: Path, stats: dict, n_pred: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "Порівняння прогнозу Калмана з реальною траєкторією \n",
        f"Кадрів з прогнозом: {n_pred}\n",
        f"Пар з валідним детектом: {stats.get('n_valid', 0)}\n",
    ]
    if stats.get("n_valid"):
        lines.extend(
            [
                f"RMSE (sqrt mean e^2)): {stats['rmse']:.4f} px\n",
                f"MAE (mean |e|):       {stats['mae']:.4f} px\n",
                f"Max |e|:              {stats['max']:.4f} px\n",
                f"Median |e|:           {stats['median']:.4f} px\n",
            ]
        )
    path.write_text("".join(lines), encoding="utf-8")
    print("[saved]", path.resolve())


def _ema_center(
    state: dict,
    raw: tuple[float, float] | None,
    prev_weight: float,
) -> tuple[float, float] | None:

    if raw is None:
        return None
    pw = float(np.clip(prev_weight, 0.0, 0.98))
    zx, zy = float(raw[0]), float(raw[1])
    if state.get("c") is None:
        state["c"] = (zx, zy)
        return state["c"]
    ox, oy = state["c"]
    state["c"] = (pw * ox + (1.0 - pw) * zx, pw * oy + (1.0 - pw) * zy)
    return state["c"]


def _center_from_result(res) -> tuple[float, float] | None:
    boxes = getattr(res, "boxes", None)
    if boxes is None or len(boxes) == 0:
        return None
    i = int(torch.argmax(boxes.conf))
    xy = boxes.xyxy[i].detach().cpu().numpy().reshape(4)
    return float(0.5 * (xy[0] + xy[2])), float(0.5 * (xy[1] + xy[3]))


def _infer_one(
    model,
    frame: np.ndarray,
    track_kw: dict,
    use_track: bool,
    args,
    use_half: bool,
    box_smooth_state: dict,
) -> tuple:
    with torch.inference_mode():
        if use_track:
            results = model.track(source=frame, persist=True, **track_kw)
        else:
            results = model.predict(source=frame, **track_kw)
    res = results[0] if isinstance(results, list) else results
    maybe_refine_or_suppress_fp(model, frame, res, args, use_half)
    smooth_primary_box_xyxy(
        res,
        box_smooth_state,
        args.bbox_ema,
        size_ema_boost=args.bbox_size_ema_boost,
        right_ema_boost=args.bbox_right_ema_boost,
        left_ema_boost=args.bbox_left_ema_boost,
    )
    expand_boxes_left(res, args.box_pad_left)
    expand_boxes_right(res, frame.shape[1], args.box_pad_right)
    expand_boxes_bottom(res, frame.shape[0], args.box_pad_bottom)
    shift_boxes_up(res, frame.shape[0], args.box_shift_up)
    raise_boxes_bottom(res, args.box_raise_bottom)
    return res


def _resize_for_show(img: np.ndarray, pmw: int) -> np.ndarray:
    if pmw <= 0:
        return img
    h, w = img.shape[:2]
    if w <= pmw:
        return img
    scale = pmw / float(w)
    nh = max(1, int(round(h * scale)))
    nw = max(1, int(round(w * scale)))
    return cv2.resize(img, (nw, nh), interpolation=cv2.INTER_AREA)


def _kalman_matrices(dt: float, q_scale: float, r_meas: float) -> tuple[np.ndarray, ...]:
    """F (4,4), H (2,4), Q (4,4), R (2,2), I (4,4) — вручну."""
    F = np.array(
        [
            [1.0, 0.0, dt, 0.0],
            [0.0, 1.0, 0.0, dt],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ],
        dtype=np.float64,
    )
    H = np.array([[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0]], dtype=np.float64)
    q = float(max(1e-6, q_scale))
    Q = np.diag([0.25 * q * dt**4, 0.25 * q * dt**4, q * dt**2, q * dt**2]).astype(np.float64)
    R = np.diag([float(max(1e-6, r_meas)), float(max(1e-6, r_meas))]).astype(np.float64)
    I4 = np.eye(4, dtype=np.float64)
    return F, H, Q, R, I4


def _finite_diff_velocities(
    measurements: list[tuple[float, float] | None],
) -> list[tuple[float, float, int]]:
  
    idx_pts: list[tuple[int, float, float]] = []
    for i, m in enumerate(measurements):
        if m is not None:
            idx_pts.append((i, float(m[0]), float(m[1])))
    out: list[tuple[float, float, int]] = []
    for j in range(1, len(idx_pts)):
        i0, x0, y0 = idx_pts[j - 1]
        i1, x1, y1 = idx_pts[j]
        gap = max(1, i1 - i0)
        out.append(((x1 - x0) / gap, (y1 - y0) / gap, gap))
    return out


def _robust_tail_velocity_for_prediction(
    measurements: list[tuple[float, float] | None],
    tail: int,
    last_spike_factor: float,
    min_speed_for_spike: float,
) -> np.ndarray:

    vlist = _finite_diff_velocities(measurements)
    if not vlist:
        return np.zeros(2, dtype=np.float64)
    arr = np.array([[vx, vy] for vx, vy, _ in vlist], dtype=np.float64)
    mags = np.linalg.norm(arr, axis=1)
    if len(arr) >= 2:
        base = np.median(mags[:-1])
        last_mag = float(mags[-1])
        if base < 1e-6:
            base = 1e-6
        if last_mag > last_spike_factor * base and last_mag > min_speed_for_spike:
            arr = arr[:-1]
            mags = mags[:-1]
    if len(arr) == 0:
        return np.zeros(2, dtype=np.float64)
    tail = max(1, int(tail))
    arr_t = arr[-tail:]
    return np.median(arr_t, axis=0).astype(np.float64)


def _clamp_vec2_max_norm(v: np.ndarray, vmax: float) -> np.ndarray:
    vmax = float(vmax)
    if vmax <= 0.0:
        return v
    m = float(np.linalg.norm(v))
    if m <= vmax or m < 1e-15:
        return v
    return (v / m) * vmax


def kalman_predict_future(
    measurements: list[tuple[float, float] | None],
    n_predict: int,
    dt: float = 1.0,
    q_scale: float = 4.0,
    r_meas: float = 25.0,
    predict_vel_damp: float = 1.0,
    frame_wh: tuple[int, int] | None = None,
    gate_chi2: float = 5.991,
    max_innovation_norm: float = 0.0,
    hist_vel_tail: int = 35,
    last_spike_factor: float = 4.0,
    min_speed_for_spike: float = 12.0,
    pred_vel_kalman_weight: float = 0.22,
    hover_speed_thresh: float = 0.0,
    hover_vel_scale: float = 0.0,
    max_pred_speed: float = 0.0,
) -> np.ndarray:
   
    T = len(measurements)
    F, H, Q, R, I4 = _kalman_matrices(dt, q_scale, r_meas)
    chi2_thr = float(max(1e-6, gate_chi2))
    max_innov = float(max(0.0, max_innovation_norm))
    wk = float(np.clip(pred_vel_kalman_weight, 0.0, 1.0))

    idx0 = next((i for i, m in enumerate(measurements) if m is not None), None)
    if idx0 is None:
        raise ValueError("Немає жодного для Калмана")

    z0x, z0y = measurements[idx0]
    x = np.array([[z0x], [z0y], [0.0], [0.0]], dtype=np.float64)
    idx1 = next((i for i, m in enumerate(measurements) if i > idx0 and m is not None), None)
    if idx1 is not None:
        dt_init = float(max(1, idx1 - idx0))
        zx, zy = measurements[idx1]
        x[2, 0] = (zx - z0x) / dt_init
        x[3, 0] = (zy - z0y) / dt_init
    P = np.diag([1e2, 1e2, 1e3, 1e3]).astype(np.float64)

    for k in range(idx0 + 1, T):
        x_pred = F @ x
        P_pred = F @ P @ F.T + Q
        m = measurements[k]
        if m is not None:
            z = np.array([[m[0]], [m[1]]], dtype=np.float64)
            y = z - H @ x_pred
            S = H @ P_pred @ H.T + R
            mah = y.T @ np.linalg.solve(S, y)
            d2 = float(mah.reshape(-1)[0])
            innov_norm = float(np.linalg.norm(y))
            use_meas = d2 <= chi2_thr and (max_innov <= 0.0 or innov_norm <= max_innov)
            if use_meas:
                K = P_pred @ H.T @ np.linalg.inv(S)
                x = x_pred + K @ y
                P = (I4 - K @ H) @ P_pred
            else:
                x = x_pred
                P = P_pred
        else:
            x = x_pred
            P = P_pred

    v_hist = _robust_tail_velocity_for_prediction(
        measurements,
        tail=hist_vel_tail,
        last_spike_factor=last_spike_factor,
        min_speed_for_spike=min_speed_for_spike,
    )
    vk = np.array([x[2, 0], x[3, 0]], dtype=np.float64)
    v_fused = wk * vk + (1.0 - wk) * v_hist
    hist_mag = float(np.linalg.norm(v_hist))
    hst = float(max(0.0, hover_speed_thresh))
    if hst > 0.0 and hist_mag < hst:
        v_fused = v_fused * float(hover_vel_scale)
    v_fused = _clamp_vec2_max_norm(v_fused, max_pred_speed)
    x[2, 0], x[3, 0] = float(v_fused[0]), float(v_fused[1])

    damp = float(np.clip(predict_vel_damp, 0.0, 1.0))
    w_img = h_img = None
    if frame_wh is not None:
        w_img, h_img = int(frame_wh[0]), int(frame_wh[1])

    pred = np.zeros((max(0, n_predict), 2), dtype=np.float64)
    for j in range(n_predict):
        x = F @ x
        if damp < 1.0:
            x[2, 0] *= damp
            x[3, 0] *= damp
        P = F @ P @ F.T + Q
        px = float((H @ x)[0, 0])
        py = float((H @ x)[1, 0])
        if w_img is not None and h_img is not None:
            px = float(np.clip(px, 0.0, float(w_img - 1)))
            py = float(np.clip(py, 0.0, float(h_img - 1)))
            x[0, 0], x[1, 0] = px, py
        pred[j, 0] = px
        pred[j, 1] = py
    return pred


def _play_segment(
    cap: cv2.VideoCapture,
    model: YOLO,
    track_kw: dict,
    use_track: bool,
    args,
    use_half: bool,
    box_smooth_state: dict,
    max_frames: int | None,
    window: str,
    seconds_per_frame: float,
    pmw: int,
    overlay_lines: list[str],
    wait_start: bool,
    center_smooth_state: dict,
    center_ema_prev: float,
    out_frame_wh: dict | None = None,
) -> list[tuple[float, float] | None]:
   
    centers: list[tuple[float, float] | None] = []
    first = True
    n_read = 0
    while max_frames is None or n_read < max_frames:
        ret, frame = cap.read()
        if not ret:
            break
        if out_frame_wh is not None and "wh" not in out_frame_wh:
            h, w = frame.shape[:2]
            out_frame_wh["wh"] = (int(w), int(h))
        res = _infer_one(model, frame, track_kw, use_track, args, use_half, box_smooth_state)
        plot_img = res.plot()
        if plot_img is None:
            plot_img = frame.copy()
        raw_c = _center_from_result(res)
        c = _ema_center(center_smooth_state, raw_c, center_ema_prev)
        centers.append(c)
        show = _resize_for_show(plot_img, pmw)
        y0 = 28
        for line in overlay_lines:
            cv2.putText(
                show,
                line,
                (10, y0),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 255, 255),
                2,
                cv2.LINE_AA,
            )
            y0 += 26
        cv2.imshow(window, show)
        if first and wait_start:
            while True:
                key = cv2.waitKey(30) & 0xFF
                if key in (32,):  # пробіл — «пуск»
                    break
            first = False
        else:
            delay = max(1, int(round(seconds_per_frame * 1000.0)))
            cv2.waitKey(delay)
        n_read += 1
    return centers


def _trajectory_plot(
    real_xy: np.ndarray,
    pred_xy: np.ndarray | None,
    title: str,
    invert_y: bool,
    invert_x: bool,
    real_label: str,
    pred_label: str | None,
    frame_wh: tuple[int, int] | None = None,
    margin: float = 8.0,
    save_path: str | None = None,
    show: bool = True,
):
    fig, ax = plt.subplots(figsize=(8, 7))
    ax.set_title(title)
    ax.set_xlabel("x, px (0 - лівий )")
    ax.set_ylabel("y, px")
    if invert_y:
        ax.invert_yaxis()
   
    if real_xy.size > 0:
        valid = ~np.isnan(real_xy[:, 0])
        starts = np.where(np.diff(np.r_[0, valid.astype(int), 0]) == 1)[0]
        ends = np.where(np.diff(np.r_[0, valid.astype(int), 0]) == -1)[0]
        first_seg = True
        for s, e in zip(starts, ends):
            seg = real_xy[s:e]
            ax.plot(
                seg[:, 0],
                seg[:, 1],
                "-",
                color="tab:blue",
                linewidth=2,
                label=real_label if first_seg else None,
            )
            first_seg = False
    if pred_xy is not None and len(pred_xy) > 0:
        ax.plot(
            pred_xy[:, 0],
            pred_xy[:, 1],
            "--",
            color="tab:orange",
            linewidth=2,
            label=pred_label,
        )
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), loc="best")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, alpha=0.3)
    if frame_wh is not None:
        w, h = frame_wh
        ax.set_xlim(-margin, float(w - 1) + margin)
        if invert_y:
            ax.set_ylim(float(h - 1) + margin, -margin)
        else:
            ax.set_ylim(-margin, float(h - 1) + margin)
    if invert_x:
        ax.invert_xaxis()
    fig.tight_layout()
    _maybe_show_save_close(fig, save_path, show)


def _trajectory_plot_graph1(
    real_half_xy: np.ndarray,
    pred_xy_raw: np.ndarray,
    pred_plot_xy: np.ndarray | None,
    title: str,
    invert_y: bool,
    invert_x: bool,
    real_label: str,
    pred_label: str,
    frame_wh: tuple[int, int] | None,
    k_pred_start: int,
    n_predict_frames: int,
    total_frames: int,
    margin: float = 8.0,
    save_path: str | None = None,
    show: bool = True,
):
    
    fig, (ax_xy, ax_t) = plt.subplots(
        2,
        1,
        figsize=(8, 9.5),
        gridspec_kw={"height_ratios": [1.55, 1.0]},
        constrained_layout=True,
    )
    fig.suptitle(title, fontsize=11)

    ax_xy.set_title("площина кадру (x, y), px")
    ax_xy.set_xlabel("x, px (0 - лівий край)")
    ax_xy.set_ylabel("y, px")
    if invert_y:
        ax_xy.invert_yaxis()

    if real_half_xy.size > 0:
        valid = ~np.isnan(real_half_xy[:, 0])
        starts = np.where(np.diff(np.r_[0, valid.astype(int), 0]) == 1)[0]
        ends = np.where(np.diff(np.r_[0, valid.astype(int), 0]) == -1)[0]
        first_seg = True
        for s, e in zip(starts, ends):
            seg = real_half_xy[s:e]
            ax_xy.plot(
                seg[:, 0],
                seg[:, 1],
                "-",
                color="tab:blue",
                linewidth=2,
                label=real_label if first_seg else None,
            )
            first_seg = False
    if pred_plot_xy is not None and len(pred_plot_xy) > 0:
        ax_xy.plot(
            pred_plot_xy[:, 0],
            pred_plot_xy[:, 1],
            "--",
            color="tab:orange",
            linewidth=2,
            label=pred_label,
        )
    h, lab = ax_xy.get_legend_handles_labels()
    by_l = dict(zip(lab, h))
    ax_xy.legend(by_l.values(), by_l.keys(), loc="best")
    ax_xy.set_aspect("equal", adjustable="box")
    ax_xy.grid(True, alpha=0.3)
    if frame_wh is not None:
        w, h = frame_wh
        ax_xy.set_xlim(-margin, float(w - 1) + margin)
        if invert_y:
            ax_xy.set_ylim(float(h - 1) + margin, -margin)
        else:
            ax_xy.set_ylim(-margin, float(h - 1) + margin)
    if invert_x:
        ax_xy.invert_xaxis()

    rng_pred = (
        f"{k_pred_start}..{k_pred_start + n_predict_frames - 1}"
        if n_predict_frames > 0
        else "—"
    )
    n_real = int(real_half_xy.shape[0])
    ax_t.set_title(
        f"Час: координати і k (суцільно: кадри 0..{max(0, n_real - 1)}  у фазі 1; пунктир: прогноз "
        f"k = {rng_pred}; N={total_frames})",
        fontsize=9,
    )
    ax_t.set_xlabel("k — індекс кадру")
    ax_t.set_ylabel("px")
    k_real = np.arange(n_real, dtype=np.float64)
    ax_t.plot(k_real, real_half_xy[:, 0], "-", color="tab:blue", linewidth=1.5, label="x реально")
    ax_t.plot(k_real, real_half_xy[:, 1], "-", color="tab:green", linewidth=1.5, label="y реально")
    if n_predict_frames > 0 and pred_xy_raw.size > 0:
        k_pred = k_pred_start + np.arange(len(pred_xy_raw), dtype=np.float64)
        ax_t.plot(
            k_pred,
            pred_xy_raw[:, 0],
            "--",
            color="tab:orange",
            linewidth=1.8,
            label="x прогноз",
        )
        ax_t.plot(
            k_pred,
            pred_xy_raw[:, 1],
            "--",
            color="darkorange",
            linewidth=1.8,
            label="y прогноз",
        )
    ax_t.axvline(float(k_pred_start) - 0.5, color="gray", linestyle=":", linewidth=1.2, label="кінець першої")
    ax_t.set_xlim(
        -0.5,
        float(max(total_frames - 1, k_pred_start + max(0, n_predict_frames - 1))) + 0.5,
    )
    ax_t.grid(True, alpha=0.3)
    h2, lab2 = ax_t.get_legend_handles_labels()
    by_t = dict(zip(lab2, h2))
    ax_t.legend(by_t.values(), by_t.keys(), loc="best", fontsize=8)

    _maybe_show_save_close(fig, save_path, show)


def main():
    torch.backends.cudnn.benchmark = True
    if torch.cuda.is_available():
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True
    torch.set_grad_enabled(False)
    cv2.setUseOptimized(True)
    cv2.setNumThreads(1)

    device_default = "cuda:0" if torch.cuda.is_available() else "cpu"
    parser = argparse.ArgumentParser(
        description="Графіки",
    )
    parser.add_argument("--video", type=str, default=str(_DEFAULT_VIDEO))
    parser.add_argument("--weights", type=str, default="yolov8x.pt")
    parser.add_argument("--imgsz", type=int, default=320)
    parser.add_argument("--conf", type=float, default=0.45)
    parser.add_argument("--iou", type=float, default=0.5)
    parser.add_argument("--device", type=str, default=device_default)
    parser.add_argument("--tracker", type=str, default="")
    parser.add_argument("--half", action="store_true")
    parser.add_argument("--no-half", action="store_true")
    parser.add_argument("--no-track", action="store_true")
    parser.add_argument("--preview-max-width", type=int, default=960)
    parser.add_argument("--playback-speed", type=float, default=1.0)
    parser.add_argument("--sync-file-fps", action="store_true")
    parser.add_argument("--bbox-ema", type=float, default=0.65)
    parser.add_argument("--bbox-size-ema-boost", type=float, default=0.10)
    parser.add_argument("--bbox-right-ema-boost", type=float, default=0.08)
    parser.add_argument("--bbox-left-ema-boost", type=float, default=0.08)
    parser.add_argument("--box-pad-bottom", type=float, default=0.18)
    parser.add_argument("--box-pad-right", type=float, default=0.06)
    parser.add_argument("--box-pad-left", type=float, default=0.06)
    parser.add_argument("--box-shift-up", type=float, default=0.04)
    parser.add_argument("--box-raise-bottom", type=float, default=0.04)
    parser.add_argument("--fp-crop-check", action="store_true")
    parser.add_argument("--fp-crop-skip-conf", type=float, default=0.54)
    parser.add_argument("--fp-crop-conf", type=float, default=0.22)
    parser.add_argument("--fp-crop-suppress-below", type=float, default=0.42)
    parser.add_argument(
        "--kalman-q",
        type=float,
        default=0.8,
        help="масштаб шуму процесу Q",
    )
    parser.add_argument(
        "--kalman-r",
        type=float,
        default=320.0,
        help="R — дисперсія шуму вимірювання",
    )
    parser.add_argument(
        "--center-ema",
        type=float,
        default=0.88,
        help="0.88 ≈ плавна траєкторія",
    )
    parser.add_argument(
        "--predict-vel-damp",
        type=float,
        default=0.981,
    )
    parser.add_argument(
        "--no-invert-plot-x",
        action="store_true",
    )
    parser.add_argument(
        "--kalman-gate-chi2",
        type=float,
        default=5.991,
        help="поріг d²=y^T S^{-1} для χ²(2)",
    )
    parser.add_argument(
        "--kalman-max-innov-px",
        type=float,
        default=95.0,
    )
    parser.add_argument(
        "--hist-vel-tail",
        type=int,
        default=40,
    )
    parser.add_argument(
        "--hist-last-spike-factor",
        type=float,
        default=4.0,
    )
    parser.add_argument(
        "--hist-min-spike-speed",
        type=float,
        default=10.0,
    )
    parser.add_argument(
        "--pred-vel-kalman-weight",
        type=float,
        default=0.1,
    )
    parser.add_argument(
        "--hover-speed-thresh",
        type=float,
        default=2.5,
    )
    parser.add_argument(
        "--hover-vel-scale",
        type=float,
        default=0.0,
        help="0 - повна зупинка прогнозу руху",
    )
    parser.add_argument(
        "--max-pred-speed",
        type=float,
        default=2.0,
    )
    parser.add_argument(
        "--plot-dir",
        type=str,
        default="trajectory_plots",
    )
    parser.add_argument(
        "--no-save-plots",
        action="store_true",
    )
    parser.add_argument(
        "--no-show-plots",
        action="store_true",
    )
    args = parser.parse_args()

    if not cv2_highgui_available():
        print(
            "[ПОМИЛКА] OpenCV",
        )
        return

    show_plots = not args.no_show_plots
    plot_dir: Path | None = None if args.no_save_plots else Path(args.plot_dir)
    if plot_dir is not None:
        plot_dir.mkdir(parents=True, exist_ok=True)

    def plot_out(name: str) -> str | None:
        return str(plot_dir / name) if plot_dir is not None else None

    use_half = (str(args.device).startswith("cuda") and not args.no_half) or (
        args.half and str(args.device).startswith("cuda")
    )
    use_track = not args.no_track

    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        print("Не відкрилося:", args.video)
        return

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    half = total_frames // 2
    src_fps = cap.get(cv2.CAP_PROP_FPS)
    if src_fps is None or src_fps < 1.0:
        src_fps = 30.0
    spd = float(max(0.05, args.playback_speed))
    seconds_per_frame = 1.0 / (src_fps * spd) if args.sync_file_fps else 0.0
    if seconds_per_frame <= 0.0:
        seconds_per_frame = 1.0 / (src_fps * spd)

    print(f"кількість кадрів: {total_frames}")
    print(f"перша фаза: {half} кадрів")
    if half <= 0:
        print(" мало кадрів у відео")
        cap.release()
        return

    model = YOLO(args.weights)
    model.to(args.device)
    try:
        model.fuse()
    except Exception:
        pass

    track_kw = dict(
        conf=float(args.conf),
        iou=float(args.iou),
        imgsz=int(args.imgsz),
        max_det=1,
        device=args.device,
        half=use_half,
        verbose=False,
        stream=False,
    )
    if args.tracker.strip():
        track_kw["tracker"] = args.tracker.strip()

    win = " trajectory "
    cv2.namedWindow(win, cv2.WINDOW_NORMAL)

    box_state1: dict = {"xyxy": None}
    center_state1: dict = {"c": None}
    frame_info: dict = {}
    overlay1 = [
        f"Phase 1/2: frames 0..{half - 1} / {total_frames}",
        "run - space",
    ]
    t0 = time.perf_counter()
    meas_first = _play_segment(
        cap,
        model,
        track_kw,
        use_track,
        args,
        use_half,
        box_state1,
        half,
        win,
        seconds_per_frame,
        int(args.preview_max_width),
        overlay1,
        wait_start=False,
        center_smooth_state=center_state1,
        center_ema_prev=float(args.center_ema),
        out_frame_wh=frame_info,
    )
    print(f"фаза 1 {len(meas_first)} за {time.perf_counter() - t0:.1f} с")

    wh = frame_info.get("wh")
    n_pred = max(0, total_frames - half)
    try:
        pred_xy = kalman_predict_future(
            meas_first,
            n_predict=n_pred,
            dt=1.0,
            q_scale=float(args.kalman_q),
            r_meas=float(args.kalman_r),
            predict_vel_damp=float(args.predict_vel_damp),
            frame_wh=wh,
            gate_chi2=float(args.kalman_gate_chi2),
            max_innovation_norm=float(args.kalman_max_innov_px),
            hist_vel_tail=int(args.hist_vel_tail),
            last_spike_factor=float(args.hist_last_spike_factor),
            min_speed_for_spike=float(args.hist_min_spike_speed),
            pred_vel_kalman_weight=float(args.pred_vel_kalman_weight),
            hover_speed_thresh=float(args.hover_speed_thresh),
            hover_vel_scale=float(args.hover_vel_scale),
            max_pred_speed=float(args.max_pred_speed),
        )
    except ValueError as e:
        print(e)
        cap.release()
        cv2.destroyAllWindows()
        return

    real_half_xy = np.array(
        [[m[0], m[1]] if m is not None else [np.nan, np.nan] for m in meas_first],
        dtype=np.float64,
    )
    
    pred_plot = pred_xy
    if n_pred > 0 and pred_xy.size > 0:
        last = None
        for m in reversed(meas_first):
            if m is not None:
                last = np.array([[m[0], m[1]]], dtype=np.float64)
                break
        if last is not None:
            pred_plot = np.vstack([last, pred_xy])

    plot_invert_x = not bool(args.no_invert_plot_x)
    if len(pred_xy) != n_pred:
        print(f"[WARN] точок прогнозу {len(pred_xy)} !=  кадрів прогнозу {n_pred}")
    _trajectory_plot_graph1(
        real_half_xy,
        pred_xy,
        pred_plot if n_pred > 0 else None,
        "графік 1",
        invert_y=True,
        invert_x=plot_invert_x,
        real_label="реально (1)",
        pred_label="прогноз",
        frame_wh=wh,
        k_pred_start=half,
        n_predict_frames=len(pred_xy),
        total_frames=total_frames,
        save_path=plot_out("graph1_half_and_pred.png"),
        show=show_plots,
    )

    box_state2: dict = {"xyxy": None}
    center_state2: dict = {"c": center_state1.get("c")}
    overlay2 = [
        f"Phase 2/2: frames {half}..{total_frames - 1}",
        "SPACE = play",
    ]
    t1 = time.perf_counter()
    meas_second = _play_segment(
        cap,
        model,
        track_kw,
        use_track,
        args,
        use_half,
        box_state2,
        max_frames=None,
        window=win,
        seconds_per_frame=seconds_per_frame,
        pmw=int(args.preview_max_width),
        overlay_lines=overlay2,
        wait_start=True,
        center_smooth_state=center_state2,
        center_ema_prev=float(args.center_ema),
        out_frame_wh=None,
    )
    print(f"фаза 2  {len(meas_second)} за {time.perf_counter() - t1:.1f} с")

    err_stats, err_rows = compute_pred_vs_real_errors(pred_xy, meas_second, half)
    if err_stats.get("n_valid"):
        print(
            "Прогноз і реальна траєкторія: "
            f"n={err_stats['n_valid']}, RMSE={err_stats['rmse']:.2f} px, "
            f"MAE={err_stats['mae']:.2f} px, max={err_stats['max']:.2f} px, "
            f"median={err_stats['median']:.2f} px",
        )
    else:
        print(
            "Похибку не порахована",
        )
    if plot_dir is not None:
        write_error_csv(plot_dir / "prediction_vs_real_error.csv", err_rows)
        write_error_summary_txt(plot_dir / "prediction_error_summary.txt", err_stats, n_pred)

    k_err = np.array([r[0] for r in err_rows], dtype=np.float64) if err_rows else np.array([])
    v_err = np.array([r[1] for r in err_rows], dtype=np.float64) if err_rows else np.array([])
    plot_prediction_error_figure(
        k_err,
        v_err,
        err_stats,
        plot_out("graph3_prediction_error.png"),
        show_plots,
    )

    cap.release()
    cv2.destroyAllWindows()

    full_meas = meas_first + meas_second
    full_xy = np.array(
        [[m[0], m[1]] if m is not None else [np.nan, np.nan] for m in full_meas],
        dtype=np.float64,
    )
    _trajectory_plot(
        full_xy,
        None,
        "графік 2",
        invert_y=True,
        invert_x=plot_invert_x,
        real_label="реально",
        pred_label=None,
        frame_wh=wh,
        save_path=plot_out("graph2_full_real.png"),
        show=show_plots,
    )


if __name__ == "__main__":
    main()
