import cv2

cap = cv2.VideoCapture("./inputs/40343737_20260313_110600_to_112100_left.mp4")
fps = cap.get(cv2.CAP_PROP_FPS)

sample_interval_seconds = 2.0
sample_every_n_frames = int(fps * sample_interval_seconds)  # cada 60 frames

frames_list = []
timestamps_list = []
frame_idx = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break  # fin del video
    
    # Solo procesamos 1 de cada N frames
    if frame_idx % sample_every_n_frames == 0:
        frames_list.append(frame)
        timestamps_list.append(frame_idx / fps)  # en segundos
    
    frame_idx += 1

cap.release()
print(f"Muestreados {len(frames_list)} frames de {frame_idx} totales")