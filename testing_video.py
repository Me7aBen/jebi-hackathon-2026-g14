import cv2

cap = cv2.VideoCapture("./inputs/40343737_20260313_110600_to_112100_left.mp4")

# Métricas del video
fps = cap.get(cv2.CAP_PROP_FPS)              # 30.0
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))  # 27000
duration_s = total_frames / fps              # 900 segundos
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

print(f"Video: {width}×{height} @ {fps}fps, {duration_s:.0f}s")

cap.release()  # siempre cierra después