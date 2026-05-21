from ultralytics import YOLO

if __name__ == '__main__':
    model = YOLO('yolov8x.pt') 

    model.train(
        data='data.yaml',   
        epochs=50,
        imgsz=640,
        batch=1,            
        device=0,
        workers=2,
        name='drone_final_results'
    )