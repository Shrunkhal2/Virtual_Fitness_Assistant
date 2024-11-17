import cv2
import mediapipe as md
import tkinter as tk
import threading
import queue
import playsound
import math
import time
import pygame

pygame.mixer.init()

cap = cv2.VideoCapture(0)

cap.set(3, 1280)  
cap.set(4, 720)   

md_drawing = md.solutions.drawing_utils
md_pose = md.solutions.pose

hold_time_threshold = 100

buzzer = r"C:\Users\nupur bhatkhande\Desktop\Relax.mp3"
welcome = r"C:\Users\nupur bhatkhande\Desktop\welcome.mp3"
motivational_music = r"C:\Users\nupur bhatkhande\Desktop\yoga_guide.mp3"

update_queue = queue.Queue()

target_count = None
music_playing = False  

buzzer_played_flag = False

gui_initialized = False

tadasana_in_progress = False

elapsed_time = 0

def play_buzzer_once():
    global buzzer_played_flag
    if not buzzer_played_flag:
        playsound.playsound(buzzer)
        buzzer_played_flag = True


def play_welcome_sound():
    playsound.playsound(welcome)


def play_motivational_music():
    global music_playing
    if not music_playing:
        pygame.mixer.music.load(motivational_music)
        pygame.mixer.music.play(0) 
        music_playing = True


def stop_motivational_music():
    global music_playing
    if music_playing:
        pygame.mixer.music.stop()
        music_playing = False


def update_gui():
    global target_count, target_label
    try:
        
        new_target = target_count.get()
        if new_target != "":
            target_label.config(text=f"Target Hold Time: {new_target} seconds")
    except ValueError:
        pass
    root.after(1000, update_gui)  


def update_target_count():
    global target_count
    new_target = target_entry.get()
    if new_target == "":
        target_count.set("")  
    try:
        if new_target == "":
            stop_motivational_music()  
        else:
            new_target = int(new_target)
            if new_target >= 0:  
                target_count.set(new_target)  
                
                if not music_playing:
                    play_motivational_music()
            else:
                print("New target count should be a non-negative integer.")
    except ValueError:
        print("Please enter a valid number.")


def calculate_angle(point1, point2, point3):
    angle_radians = math.atan2(point3[1] - point2[1], point3[0] - point2[0]) - math.atan2(point1[1] - point2[1], point1[0] - point2[0])
    angle_degrees = math.degrees(angle_radians)
    angle_degrees = (angle_degrees + 360) % 360  
    return angle_degrees


def run_tadasana_detection():
    global tadasana_in_progress, tadasana_start_time, audio_played_flag, update_queue, elapsed_time

    with md_pose.Pose(
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7) as pose:

        while cap.isOpened():
            success, image = cap.read()
            if not success:
                print("Empty camera")
                break

            result = pose.process(image)

           
            full_body_in_correct_position = False

            if result.pose_landmarks:
                md_drawing.draw_landmarks(
                    image, result.pose_landmarks, md_pose.POSE_CONNECTIONS)

                
                left_shoulder = result.pose_landmarks.landmark[md_pose.PoseLandmark.LEFT_SHOULDER]
                left_elbow = result.pose_landmarks.landmark[md_pose.PoseLandmark.LEFT_ELBOW]
                left_wrist = result.pose_landmarks.landmark[md_pose.PoseLandmark.LEFT_WRIST]

                
                angle_shoulder_elbow_wrist = calculate_angle(
                    (left_shoulder.x, left_shoulder.y),
                    (left_elbow.x, left_elbow.y),
                    (left_wrist.x, left_wrist.y)
                )

                
                if angle_shoulder_elbow_wrist > 175 and left_wrist.y < left_shoulder.y:
                    cv2.rectangle(image, (10, 10), (100, 40), (0, 255, 0), -1)  # Green rectangle for correct posture
                    cv2.putText(image, "Correct Posture", (120, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                    if not tadasana_in_progress:
                        tadasana_start_time = time.time()
                        tadasana_in_progress = True
                        audio_played_flag = False

                    elapsed_time = time.time() - tadasana_start_time

                    if elapsed_time >= hold_time_threshold and not audio_played_flag:
                        
                        update_queue.put(elapsed_time)
                        tadasana_in_progress = False
                        audio_played_flag = True

                else:
                    cv2.rectangle(image, (10, 10), (100, 40), (0, 0, 255), -1)  # Red rectangle for incorrect posture
                    cv2.putText(image, "Incorrect Posture", (120, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    
                    cv2.putText(image, "Please maintain a correct Tadasana posture", (120, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                    
                    tadasana_start_time = None
                    tadasana_in_progress = False
                    audio_played_flag = False

            cv2.imshow("Tadasana Detector", image)

            try:
                
                new_target = target_count.get()
                if new_target != "" and elapsed_time >= float(new_target):
                    play_buzzer_once()  
            except ValueError:
                pass

            key = cv2.waitKey(1)
            if key == ord('q'):
                break


def run_gui():
    global target_entry, target_count, target_label, root, gui_initialized

    root = tk.Tk()
    root.title("Tadasana Detector")
    root.geometry("400x200")
    root.configure(bg="#f0f0f0")  

    frame = tk.Frame(root, bg="#ffffff", padx=20, pady=20)  
    frame.pack(expand=True, fill="both")

    label = tk.Label(frame, text="Set Your Tadasana Hold Time (sec)", font=("Helvetica", 14), bg="#ffffff")
    label.pack()

    target_entry = tk.Entry(frame, font=("Helvetica", 12))
    target_entry.insert(0, "10")  
    target_entry.pack()

    set_button = tk.Button(frame, text="Set Hold Time", command=update_target_count, bg="#007acc", fg="#ffffff", font=("Helvetica", 12))
    set_button.pack()

    target_count = tk.StringVar(value="")  
    target_label = tk.Label(frame, textvariable=target_count, font=("Helvetica", 12), bg="#ffffff")
    target_label.pack()

    update_gui()  
    gui_initialized = True

    root.mainloop()

gui_thread = threading.Thread(target=run_gui)
gui_thread.start()

play_welcome_sound()

tadasana_thread = threading.Thread(target=run_tadasana_detection)
tadasana_thread.start()

gui_thread.join()

stop_motivational_music()

cap.release()
cv2.destroyAllWindows()
