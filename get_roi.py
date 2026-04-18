import cv2

cap = cv2.VideoCapture("./inputs/40343737_20260313_110600_to_112100_left.mp4")
# Saltar al frame 1000 (=33.33 segundos, probable momento con camión visible)
cap.set(cv2.CAP_PROP_POS_FRAMES, 1000)
ret, frame = cap.read()
cv2.imwrite("sample_frame.png", frame)
cap.release()