# -*- coding: utf-8 -*-


import argparse
import time
from pathlib import Path

import cv2
import numpy as np
import torch
from ultralytics import YOLO

_SCRIPT_DIR = Path(__file__).resolve().parent
_DEFAULT_VIDEO = _SCRIPT_DIR / "test" / "pexels-joseph-redfield-8459631 (1080p).mp4"


def maybe_refine_or_suppress_fp(model, frame, result, args, use_half):
   
    if not args.fp_crop_check:
        return
    boxes = getattr(result, "boxes", None)
    if boxes is None or len(boxes) == 0:
        return
    i = int(torch.argmax(boxes.conf))
    c0 = float(boxes.conf[i])
    if c0 >= float(args.fp_crop_skip_conf):
        return
    xy = boxes.xyxy[i].detach().cpu().numpy().reshape(4)
    h, w = frame.shape[:2]
    cx = 0.5 * (xy[0] + xy[2])
    cy = 0.5 * (xy[1] + xy[3])
    bw = max(8.0, float(xy[2] - xy[0]))
    bh = max(8.0, float(xy[3] - xy[1]))
    pad = 0.38
    x1 = int(max(0, cx - bw * (0.5 + pad)))
    y1 = int(max(0, cy - bh * (0.5 + pad)))
    x2 = int(min(w - 1, cx + bw * (0.5 + pad)))
    y2 = int(min(h - 1, cy + bh * (0.5 + pad)))
    if x2 <= x1 + 16 or y2 <= y1 + 16:
        return
    crop = frame[y1 : y2 + 1, x1 : x2 + 1]
    imgsz2 = min(640, int(args.imgsz) + 160)
    r2 = model.predict(
        source=crop,
        conf=float(args.fp_crop_conf),
        iou=float(args.iou),
        imgsz=imgsz2,
        max_det=1,
        device=args.device,
        half=use_half,
        verbose=False,
        stream=False,
    )[0]
    b2 = getattr(r2, "boxes", None)
    d = result.boxes.data
    if b2 is None or len(b2) == 0:
        if c0 < float(args.fp_crop_suppress_below):
            result.boxes.data = d[:0]
        return
    row = b2.data[0].clone()
    row[0] += float(x1)
    row[2] += float(x1)
    row[1] += float(y1)
    row[3] += float(y1)
    result.boxes.data = row.unsqueeze(0)


def cv2_highgui_available():
    """False """
    try:
        cv2.namedWindow("_cv_gui_probe", cv2.WINDOW_NORMAL)
        cv2.destroyWindow("_cv_gui_probe")
        return True
    except cv2.error:
        return False


def smooth_primary_box_xyxy(
    result,
    state,
    prev_weight,
    size_ema_boost=0.10,
    right_ema_boost=0.08,
    left_ema_boost=0.08,
):
    boxes = getattr(result, "boxes", None)
    if boxes is None or len(boxes) == 0:
        state["xyxy"] = None
        return
    pw = float(np.clip(prev_weight, 0.0, 0.95))
    pw_size = float(np.clip(pw - float(size_ema_boost), 0.0, 0.95))
    pw_side = float(np.clip(pw - float(size_ema_boost), 0.0, 0.95))
    pw_left = float(np.clip(pw_side - float(left_ema_boost), 0.0, 0.95))
    pw_right = float(np.clip(pw_side - float(right_ema_boost), 0.0, 0.95))
    i = int(torch.argmax(boxes.conf))
    xy = boxes.xyxy[i].detach().float().cpu().numpy().astype(np.float64)
    if state["xyxy"] is None or pw <= 0.0:
        state["xyxy"] = xy.copy()
    else:
        old = state["xyxy"]
        state["xyxy"] = np.array(
            [
                pw_left * old[0] + (1.0 - pw_left) * xy[0],
                pw_size * old[1] + (1.0 - pw_size) * xy[1],
                pw_right * old[2] + (1.0 - pw_right) * xy[2],
                pw_size * old[3] + (1.0 - pw_size) * xy[3],
            ],
            dtype=np.float64,
        )
    d = boxes.data.clone()
    d[i, :4] = torch.as_tensor(state["xyxy"], device=d.device, dtype=d.dtype)
    boxes.data = d


def expand_boxes_left(result, rel_pad):
    boxes = getattr(result, "boxes", None)
    if boxes is None or len(boxes) == 0:
        return
    rel_pad = float(rel_pad)
    if rel_pad == 0.0:
        return
    d = boxes.data.clone()
    x1, x2 = d[:, 0], d[:, 2]
    bw = torch.clamp(x2 - x1, min=1.0)
    x1_new = x1 - rel_pad * bw
    x1_new = torch.maximum(x1_new, torch.zeros_like(x1_new))
    d[:, 0] = torch.minimum(x1_new, x2 - 1.0)
    boxes.data = d


def expand_boxes_right(result, im_w, rel_pad):
    boxes = getattr(result, "boxes", None)
    if boxes is None or len(boxes) == 0:
        return
    rel_pad = float(rel_pad)
    if rel_pad == 0.0:
        return
    d = boxes.data.clone()
    x1, x2 = d[:, 0], d[:, 2]
    bw = torch.clamp(x2 - x1, min=1.0)
    x2_new = x2 + rel_pad * bw
    x2_new = torch.minimum(x2_new, torch.full_like(x2_new, float(im_w - 1)))
    d[:, 2] = torch.maximum(x2_new, x1 + 1.0)
    boxes.data = d


def expand_boxes_bottom(result, im_h, rel_pad):
    boxes = getattr(result, "boxes", None)
    if boxes is None or len(boxes) == 0:
        return
    rel_pad = float(rel_pad)
    if rel_pad == 0.0:
        return
    d = boxes.data.clone()
    y1, y2 = d[:, 1], d[:, 3]
    bh = torch.clamp(y2 - y1, min=1.0)
    y2_new = y2 + rel_pad * bh
    y2_new = torch.minimum(y2_new, torch.full_like(y2_new, float(im_h - 1)))
    d[:, 3] = torch.maximum(y2_new, y1 + 1.0)
    boxes.data = d


def shift_boxes_up(result, im_h, rel_shift):
    boxes = getattr(result, "boxes", None)
    if boxes is None or len(boxes) == 0:
        return
    rel_shift = float(rel_shift)
    if rel_shift == 0.0:
        return
    d = boxes.data.clone()
    y1, y2 = d[:, 1], d[:, 3]
    bh = torch.clamp(y2 - y1, min=1.0)
    dy = rel_shift * bh
    y1_new = torch.clamp(y1 - dy, min=0.0)
    y2_new = torch.clamp(y2 - dy, max=float(im_h - 1))
    d[:, 1] = y1_new
    d[:, 3] = torch.maximum(y2_new, y1_new + 1.0)
    boxes.data = d


def raise_boxes_bottom(result, rel_raise):
    boxes = getattr(result, "boxes", None)
    if boxes is None or len(boxes) == 0:
        return
    rel_raise = float(rel_raise)
    if rel_raise == 0.0:
        return
    d = boxes.data.clone()
    y1, y2 = d[:, 1], d[:, 3]
    bh = torch.clamp(y2 - y1, min=1.0)
    y2_new = y2 - rel_raise * bh
    d[:, 3] = torch.maximum(y2_new, y1 + 1.0)
    boxes.data = d


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
        description="Drone tracking YOLOv8",
    )
    parser.add_argument(
        "--video",
        type=str,
        default=str(_DEFAULT_VIDEO),
        help=f"за замовчуванням: {_DEFAULT_VIDEO.name} ",
    )
    parser.add_argument("--weights", type=str, default="yolov8x.pt")
    parser.add_argument(
        "--imgsz",
        type=int,
        default=320,
        help=" 416–640 ",
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.45,
        help="поріг (0.3)",
    )
    parser.add_argument(
        "--iou",
        type=float,
        default=0.5,
        help="IoU для NMS",
    )
    parser.add_argument("--device", type=str, default=device_default)
    parser.add_argument(
        "--tracker",
        type=str,
        default="",
        help="ultralytics",
    )
    parser.add_argument("--show-fps", action="store_true")
    parser.add_argument("--half", action="store_true")
    parser.add_argument("--no-half", action="store_true")
    parser.add_argument("--preview-max-width", type=int, default=960, help="0 = без зміни розміру вікна")
    parser.add_argument(
        "--out-video",
        type=str,
        default="",
        help=" ",
    )
    parser.add_argument("--max-speed", action="store_true")
    parser.add_argument("--playback-speed", type=float, default=1.0)
    parser.add_argument(
        "--sync-file-fps",
        action="store_true",
        help="синхронізувати з FPS файлу",
    )
    parser.add_argument("--diag", action="store_true")
    parser.add_argument("--diag-out", type=str, default="drone_timing_log.txt")
    parser.add_argument(
        "--no-track",
        action="store_true",
        help=" predict, без трекера",
    )
    parser.add_argument(
        "--box-pad-bottom",
        type=float,
        default=0.18,
        help="зсув нижнього краю bbox (частка висоти; <0 піднімає кути)",
    )
    parser.add_argument(
        "--box-shift-up",
        type=float,
        default=0.04,
        help="підняти центр рамки вгору (частка висоти bbox)",
    )
    parser.add_argument(
        "--box-raise-bottom",
        type=float,
        default=0.04,
        help="підняти нижні кути (лівий і правий), зменшити y2",
    )
    parser.add_argument(
        "--box-pad-right",
        type=float,
        default=0.06,
        help="розширити правий край bbox (частка ширини; лопасті справа)",
    )
    parser.add_argument(
        "--box-pad-left",
        type=float,
        default=0.06,
        help="розширити лівий край bbox (частка ширини; лопасті зліва)",
    )
    parser.add_argument(
        "--bbox-ema",
        type=float,
        default=0.65,
        help="EMA центру рамки (0 = вимк)",
    )
    parser.add_argument(
        "--bbox-size-ema-boost",
        type=float,
        default=0.10,
        help="швидше оновлення ширини/висоти (зменшує pw_size на цю величину)",
    )
    parser.add_argument(
        "--bbox-right-ema-boost",
        type=float,
        default=0.08,
        help="ще швидше оновлення правого краю x2 (поверх size-ema-boost)",
    )
    parser.add_argument(
        "--bbox-left-ema-boost",
        type=float,
        default=0.08,
        help="ще швидше оновлення лівого краю x1 (поверх size-ema-boost)",
    )
    parser.add_argument(
        "--fp-crop-check",
        action="store_true",
        help=" ",
    )
    parser.add_argument(
        "--fp-crop-skip-conf",
        type=float,
        default=0.54,
        help=" другий прохід не робити, якщо conf≥",
    )
    parser.add_argument(
        "--fp-crop-conf",
        type=float,
        default=0.22,
        help="поріг для другого",
    )
    parser.add_argument(
        "--fp-crop-suppress-below",
        type=float,
        default=0.42,
        help=" ",
    )
    args = parser.parse_args()

    use_half = (str(args.device).startswith("cuda") and not args.no_half) or (
        args.half and str(args.device).startswith("cuda")
    )
    use_track = not args.no_track

    max_speed = args.max_speed or (
        str(args.device).startswith("cpu") and not args.sync_file_fps
    )

    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        print("Не відкрилося:", args.video)
        return

    src_fps = cap.get(cv2.CAP_PROP_FPS)
    if src_fps is None or src_fps < 1.0:
        src_fps = 30.0
    spd = float(max(0.05, args.playback_speed))
    seconds_per_frame = 1.0 / (src_fps * spd)

    out_path = (args.out_video or "").strip()
    use_gui = not bool(out_path)
    if use_gui and not cv2_highgui_available():
        print(
            "[ПОМИЛКА] OpenCV (cv2.imshow)",
        )
        print("  pip uninstall opencv-python-headless -y  &&  pip install opencv-python")
        print('  або:  --out-video "preview_out.mp4"')
        cap.release()
        return
    if out_path:
        print("[INFO] запис у файл:", out_path)

    print("CUDA:", torch.cuda.is_available(), "| device:", args.device)
    print(
        "conf=", args.conf, "iou=", args.iou, "| imgsz:", args.imgsz, "| track:", use_track,
        "| fp-crop-check:", args.fp_crop_check,
    )

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

    fps_real_ema = 0.0
    fps_stat_t = time.perf_counter()
    fps_stat_n = 0
    overload_warn_printed = False
    diag_samples = [] if args.diag else None
    box_smooth_state = {"xyxy": None}
    writer = None

    while True:
        t_loop = time.perf_counter()

        t0 = time.perf_counter()
        ret, frame = cap.read()
        t_read = time.perf_counter() - t0
        if not ret:
            break

        t_scale = 0.0

        t0 = time.perf_counter()
        try:
            with torch.inference_mode():
                if use_track:
                    results = model.track(source=frame, persist=True, **track_kw)
                else:
                    results = model.predict(source=frame, **track_kw)
        except Exception as e:
            print("infer:", e)
            t_infer = time.perf_counter() - t0
            if diag_samples is not None:
                diag_samples.append(
                    {
                        "read_ms": t_read * 1000.0,
                        "scale_ms": t_scale * 1000.0,
                        "infer_ms": t_infer * 1000.0,
                        "compose_ms": 0.0,
                        "imshow_wait_ms": 0.0,
                        "total_ms": (time.perf_counter() - t_loop) * 1000.0,
                        "sleep_ms": 0.0,
                    }
                )
            break

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
        plot_img = res.plot()
        if plot_img is None:
            plot_img = frame.copy()
        t_infer = time.perf_counter() - t0

        t_comp_start = time.perf_counter()
        show = plot_img
        pmw = int(args.preview_max_width)
        if pmw > 0:
            fh, fw = show.shape[:2]
            if fw > pmw:
                sc = pmw / float(fw)
                show = cv2.resize(show, (int(fw * sc), int(fh * sc)), interpolation=cv2.INTER_AREA)

        if args.show_fps:
            fps_stat_n += 1
            ts = time.perf_counter()
            elapsed_stat = ts - fps_stat_t
            if elapsed_stat >= 0.5:
                inst_real = fps_stat_n / elapsed_stat
                fps_real_ema = inst_real if fps_real_ema == 0.0 else (
                    0.75 * fps_real_ema + 0.25 * inst_real
                )
                fps_stat_t = ts
                fps_stat_n = 0
            line = f"FACT {fps_real_ema:.1f} fps | file claims {src_fps:.0f} fps"
            cv2.putText(
                show,
                line,
                (20, 28),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (0, 255, 255),
                2,
            )

        t_compose = time.perf_counter() - t_comp_start

        if out_path:
            if writer is None:
                oh, ow = show.shape[:2]
                writer = cv2.VideoWriter(
                    out_path,
                    cv2.VideoWriter_fourcc(*"mp4v"),
                    float(src_fps),
                    (ow, oh),
                )
                if not writer.isOpened():
                    print("[ПОМИЛКА] VWriter не відкрився:", out_path)
                    cap.release()
                    if writer is not None:
                        writer.release()
                    return
            writer.write(show)

        t_ui_start = time.perf_counter()
        if use_gui:
            try:
                cv2.imshow("Drone Tracking (YOLOv8)", show)
                if cv2.waitKey(1) & 0xFF == 27:
                    break
            except cv2.error as e:
                print("[ПОМИЛКА] imshow:", e)
                break
        t_ui = time.perf_counter() - t_ui_start

        spent = time.perf_counter() - t_loop

        if diag_samples is not None:
            diag_samples.append(
                {
                    "read_ms": t_read * 1000.0,
                    "scale_ms": t_scale * 1000.0,
                    "infer_ms": t_infer * 1000.0,
                    "compose_ms": t_compose * 1000.0,
                    "imshow_wait_ms": t_ui * 1000.0,
                    "total_ms": spent * 1000.0,
                    "sleep_ms": 0.0,
                }
            )

        if (
            not max_speed
            and spent > seconds_per_frame * 1.05
            and not overload_warn_printed
        ):
            print(
                "[INFO] кадр довший ніж час згідно FPS файлу (",
                int(spent * 1000),
                "ms vs",
                int(seconds_per_frame * 1000),
                "ms).",
            )
            overload_warn_printed = True

        t_sleep = 0.0
        if not max_speed:
            wait = seconds_per_frame - spent
            if wait > 0:
                time.sleep(wait)
                t_sleep = wait
        if diag_samples is not None and diag_samples:
            diag_samples[-1]["sleep_ms"] = t_sleep * 1000.0
            diag_samples[-1]["total_ms"] = (time.perf_counter() - t_loop) * 1000.0

    cap.release()
    if writer is not None:
        writer.release()
        print("Відео:", out_path)
    if use_gui:
        try:
            cv2.destroyAllWindows()
        except cv2.error:
            pass

    if args.diag and diag_samples:
        lines = [
            "таймінги кадру (мс)",
            f"кадрів: {len(diag_samples)}",
            f"CUDA: {torch.cuda.is_available()} device={args.device}",
            f"conf={args.conf} iou={args.iou} imgsz={args.imgsz} bbox_ema={args.bbox_ema} track={use_track}",
            "",
        ]
        keys = ["read_ms", "scale_ms", "infer_ms", "compose_ms", "imshow_wait_ms", "sleep_ms", "total_ms"]
        for k in keys:
            vals = [s[k] for s in diag_samples if k in s]
            if not vals:
                continue
            arr = np.array(vals, dtype=np.float64)
            lines.append(f"{k}: mean={arr.mean():.2f} p95={np.percentile(arr, 95):.2f} max={arr.max():.2f}")
        report = "\n".join(lines)
        print("\n--- DIAG ---\n", report)
        try:
            with open(args.diag_out, "w", encoding="utf-8") as f:
                f.write(report)
            print("Збережено:", args.diag_out)
        except OSError as e:
            print("Не записалася diag:", e)


if __name__ == "__main__":
    main()
