import cv2
import mediapipe as mp
import tkinter as tk
import threading
import queue
import pyttsx3
import pygame
from playsound import playsound
import math


pygame.mixer.init()


cap = cv2.VideoCapture(0)


cap.set(3, 1280)  # Width
cap.set(4, 720)   # Height

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

count = 0
posture_maintained_flag = False


buzzer = r"C:\Users\nupur bhatkhande\Desktop\buzzer.mp3"
welcome = r"C:\Users\nupur bhatkhande\Desktop\welcome.mp3"
motivational_music = r"C:\Users\nupur bhatkhande\Desktop\guide.mp3" 


engine = pyttsx3.init()


update_queue = queue.Queue()


target_count = None
audio_played_flag = False
music_playing = False  


buzzer_played_flag = False


def play_buzzer_once():
    global buzzer_played_flag
    if not buzzer_played_flag:
        playsound(buzzer)
        buzzer_played_flag = True


def voice_coaching_shoulder_press_count():
    global count
    while True:
        try:
            new_count = update_queue.get()
            if new_count is not None:
                count = new_count
                engine.say(str(count))
                engine.runAndWait()
        except queue.Empty:
            pass


def play_welcome_sound():
    playsound(welcome)


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
    angle_degrees = (angle_degrees + 360) % 360  # Ensure the angle is positive
    return angle_degrees


def run_gui():
    global target_entry, target_count
    root = tk.Tk()
    root.title("Shoulder Press Counter")
    root.geometry("400x200")
    root.configure(bg="#f0f0f0")  # Set a background color

    frame = tk.Frame(root, bg="#ffffff", padx=20, pady=20)  # Create a frame with padding
    frame.pack(expand=True, fill="both")

    label = tk.Label(frame, text="Set Your Shoulder Press Target", font=("Helvetica", 14), bg="#ffffff")
    label.pack()

    target_entry = tk.Entry(frame, font=("Helvetica", 12))
    target_entry.insert(0, "10")  # Default value
    target_entry.pack()

    set_button = tk.Button(frame, text="Set Target", command=update_target_count, bg="#007acc", fg="#ffffff", font=("Helvetica", 12))
    set_button.pack()

    target_count = tk.StringVar(value="")  # Initialize target count as empty initially
    target_label = tk.Label(frame, textvariable=target_count, font=("Helvetica", 12), bg="#ffffff")
    target_label.pack()

    root.mainloop()


gui_thread = threading.Thread(target=run_gui)
gui_thread.start()


voice_coaching_thread = threading.Thread(target=voice_coaching_shoulder_press_count)
voice_coaching_thread.daemon = True
voice_coaching_thread.start()


play_welcome_sound()

with mp_pose.Pose(
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7) as pose:
    while cap.isOpened():
        success, image = cap.read()
        if not success:
            print("Empty camera")
            break

        result = pose.process(image)

        if result.pose_landmarks:
            mp_drawing.draw_landmarks(
                image, result.pose_landmarks, mp_pose.POSE_CONNECTIONS)

            
            left_elbow = result.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_ELBOW]
            left_shoulder = result.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER]
            right_elbow = result.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_ELBOW]
            right_shoulder = result.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER]

            
            if left_elbow.y > left_shoulder.y and right_elbow.y > right_shoulder.y:
                cv2.rectangle(image, (10, 10), (200, 40), (0, 255, 0), -1)  
                cv2.putText(image, "Correct Shoulder Press Posture", (220, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            else:
                cv2.rectangle(image, (10, 10), (200, 40), (0, 0, 255), -1)  
                cv2.putText(image, "Incorrect Shoulder Press Posture", (220, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                
                cv2.putText(image, "Please maintain a correct shoulder press posture", (220, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

           
            if left_elbow.y > left_shoulder.y and right_elbow.y > right_shoulder.y and not audio_played_flag:
                # Increment count only if the posture is correct and audio hasn't been played
                if not posture_maintained_flag:
                    count += 1
                    audio_played_flag = True
                    print("Shoulder Press Count:", count)
                    # Queue the count for voice coaching for shoulder press
                    update_queue.put(count)
                    posture_maintained_flag = True
            elif left_elbow.y <= left_shoulder.y or right_elbow.y <= right_shoulder.y:
                # Reset the audio_played_flag when transitioning to incorrect posture for shoulder press
                audio_played_flag = False
                posture_maintained_flag = False

        cv2.imshow("shoulder press counter", image)

        try:
            # Check if the target is updated
            new_target = target_count.get()
            if new_target != "" and count >= int(new_target):
                play_buzzer_once()  # Play the buzzer sound only once when the target is reached
        except ValueError:
            pass

        key = cv2.waitKey(1)
        if key == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()