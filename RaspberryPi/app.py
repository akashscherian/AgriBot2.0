import numpy as np
import base64
from io import BytesIO
from PIL import Image
import threading
import cv2
import time
#import random
import os
import RPi.GPIO as GPIO     # Import Library to access GPIO PIN

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

Motor_In1 = 29 # GPIO 5
Motor_In2 = 31 # GPIO 6
Motor_In3 = 33 # GPIO 13
Motor_In4 = 35 # GPIO 19
Relay_PIN = 7  # GPIO 4
SOIL_MOISTURE_PIN = 12 # GPIO 18

GPIO.setup(Motor_In1,GPIO.OUT)   # Set pin function as output
GPIO.setup(Motor_In2,GPIO.OUT)   # Set pin function as output
GPIO.setup(Motor_In3,GPIO.OUT)   # Set pin function as output
GPIO.setup(Motor_In4,GPIO.OUT)   # Set pin function as output
GPIO.setup(Relay_PIN,GPIO.OUT)   # Set pin function as output
GPIO.setup(SOIL_MOISTURE_PIN, GPIO.IN) # Set pin function as input

GPIO.output(Motor_In1, False)
GPIO.output(Motor_In2, False)
GPIO.output(Motor_In3, False)
GPIO.output(Motor_In4, False)
GPIO.output(Relay_PIN, False)

script_dir = os.path.dirname(os.path.abspath(__file__))
templates_path = os.path.join(script_dir, 'templates')
static_path = os.path.join(script_dir, 'static')
test_folder_path = os.path.join(script_dir, 'Test')

from flask import Flask, redirect, url_for, request,render_template,Response, jsonify
# Create two Flask instances
#app1 = Flask(__name__)
#app2 = Flask(__name__)
app1 = Flask(__name__, template_folder=templates_path, static_folder=static_path)
app2 = Flask(__name__, template_folder=templates_path, static_folder=static_path)

# Initialize video capture
video_capture = cv2.VideoCapture(0) # '0' for Primary Camera, '1' for USB Camera

frame = None  # Global variable to hold the current frame

def capture_video():
    global frame
    while True:
        ret, current_frame = video_capture.read()
        if not ret:
            print("Failed to capture image")
            continue  # Skip if capture failed
        frame = current_frame  # Store the captured frame

# Start the video capture thread
capture_thread = threading.Thread(target=capture_video)
capture_thread.daemon = True  # Daemonize the thread to ensure it stops when the app exits
capture_thread.start()

# Function to generate frames for streaming
def generate_frames():
    global frame
    while True:
        if frame is None:
            time.sleep(0.1)  # Wait for the first frame to be captured
            continue
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

# Video streaming route
@app1.route('/video_feed') #8080
@app2.route('/video_feed') #8088
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Move functions (these are examples and should be implemented as needed)
def move_forward():
    print("Moving forward")
    GPIO.output(Motor_In1, True)
    GPIO.output(Motor_In2, False)
    GPIO.output(Motor_In3, True)
    GPIO.output(Motor_In4, False)
    #time.sleep(0.1)

def move_backward():
    print("Moving backward")
    GPIO.output(Motor_In1, False)
    GPIO.output(Motor_In2, True)
    GPIO.output(Motor_In3, False)
    GPIO.output(Motor_In4, True)
    #time.sleep(0.1)

def move_left():
    print("Moving left")
    GPIO.output(Motor_In1, False)
    GPIO.output(Motor_In2, True)
    GPIO.output(Motor_In3, True)
    GPIO.output(Motor_In4, False)
    #time.sleep(0.1)

def move_right():
    print("Moving right")
    GPIO.output(Motor_In1, True)
    GPIO.output(Motor_In2, False)
    GPIO.output(Motor_In3, False)
    GPIO.output(Motor_In4, True)
    #time.sleep(0.1)
    
def stop_action():
    print("Stopping")
    GPIO.output(Motor_In1, False)
    GPIO.output(Motor_In2, False)
    GPIO.output(Motor_In3, False)
    GPIO.output(Motor_In4, False)
    GPIO.output(Relay_PIN, False)
    #time.sleep(0.1)

def pump_operate():
    print ("Turning ON Pump")
    GPIO.output(Relay_PIN, True)
    #time.sleep(0.1)
	
# Button actions, handled in background threads
@app1.route('/Forward', methods=['POST', 'GET'])
def Forward():
    move_forward()
    time.sleep(1)
    stop_action()
    #threading.Thread(target=move_forward).start()
    return render_template("robot.html", HTML_address=Url_Address)

@app1.route('/Backward',methods = ['POST', 'GET'])
def Backward():
    move_backward()
    time.sleep(0.5)
    stop_action()
    #threading.Thread(target=move_backward).start()
    return render_template("robot.html", HTML_address=Url_Address)

@app1.route('/Left',methods = ['POST', 'GET'])
def Left():
    move_left()
    time.sleep(0.5)
    stop_action()
    ###threading.Thread(target=move_left).start()
    return render_template("robot.html", HTML_address=Url_Address)

@app1.route('/Right',methods = ['POST', 'GET'])
def Right():
    move_right()
    time.sleep(0.5)
    stop_action()
    #threading.Thread(target=move_right).start()
    return render_template("robot.html", HTML_address=Url_Address)

@app1.route('/Stop',methods = ['POST', 'GET'])
def Stop():
    stop_action()
    #threading.Thread(target=stop_action).start()
    return render_template("robot.html", HTML_address=Url_Address)
	
@app1.route('/get_soil_moisture')
def get_soil_moisture():
    # Generate a mock soil moisture value
    #soil_moisture = random.randint(0, 100)
    if GPIO.input(SOIL_MOISTURE_PIN):
        soil_moisture = 'Dry'
    else:
        soil_moisture = 'Wet'
    print ("Soil moistur value: ",soil_moisture)
    return jsonify({'soil_moisture': soil_moisture})

@app1.route('/Pump',methods = ['POST', 'GET'])
def Pump():
   pump_operate()
   #threading.Thread(target=pump_operate).start()
   return render_template("robot.html", HTML_address=Url_Address)


from keras.models import load_model
from werkzeug.utils import secure_filename
from tensorflow.keras.preprocessing.image import load_img, img_to_array

model_path = os.path.join(script_dir, 'model.h5')
model = load_model(model_path)

# model = load_model('model.h5')

labels = {0: 'Healthy', 1: 'Powdery', 2: 'Rust'}

def getResult(image_path):
    img = load_img(image_path, target_size=(225,225))
    x = img_to_array(img)
    x = x.astype('float32') / 255.
    x = np.expand_dims(x, axis=0)
    predictions = model.predict(x)[0]
    return predictions

test_model_path = os.path.join(test_folder_path, 'test')
# Helper function to rename old files
def rename_old_file(base_name=test_model_path, extension=".jpg"):
    if os.path.exists(f"{base_name}{extension}"):
        i = 1
        while os.path.exists(f"{base_name}{i}{extension}"):
            i += 1
        os.rename(f"{base_name}{extension}", f"{base_name}{i}{extension}")

@app2.route('/capture', methods=['POST'])
def capture():
    data = request.get_json()
    image_data = data['image']
    
    try:
        # Decode the base64 image
        img_str = image_data.split(',')[1]
        img_bytes = base64.b64decode(img_str)
        img = Image.open(BytesIO(img_bytes))

        # Convert to RGB format if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # Rename old test.jpg to test1.jpg, test2.jpg, etc.
        rename_old_file()

        # Save the new image as test.jpg
        # new_image_path = "Test//test.jpg"
        new_image_path = os.path.join(test_folder_path, 'test.jpg')
        img.save(new_image_path)

        # Return the path of the saved image
        return jsonify({"path": new_image_path}), 200
    except Exception as e:
        print("Error saving image:", e)
        return jsonify({"error": str(e)}), 500


# Route to handle prediction using saved test.jpg image
@app2.route('/predict', methods=['POST'])
def predict():
    # Load the saved image
    # image_path = "Test//test.jpg"
    image_path = os.path.join(test_folder_path, 'test.jpg')
    img = Image.open(image_path)
    img = np.array(img)
    
    # Print file path for debugging purposes
    print("File path for prediction:", image_path)
    predictions=getResult(image_path)
    predicted_label = labels[np.argmax(predictions)]

    # Make prediction
    #result = predict_leaf(img)
    
    # Return prediction result to Webpage
    return jsonify({"result": predicted_label})

# Python Program to Get IP Address
import socket
# Automatically fetch the PC/Laptop's local IP address
#hostname = socket.gethostname() # Works on PC/Laptop
#Url_Address = socket.gethostbyname(hostname)
#print("URL Address :", Url_Address)

# Automatically fetch the Raspberry Pi's local IP address
def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        # doesn't have to be reachable
        s.connect(('10.254.254.254', 1))  
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

Url_Address =  get_ip_address()
   
# Route to render the index page 8080
@app1.route('/')
def index1():
   return render_template("robot.html",HTML_address=Url_Address)      
 
@app2.route('/') #8088
def index2():
    return render_template('leaf.html',HTML_address=Url_Address) 


# Function to run the first app on port 8080
def run_app1():
    app1.run(Url_Address,8080,threaded=True)
    '''try:
        app1.run(host=Url_Address, port=8080, debug=True, use_reloader=False)
    finally:
        # Release the video capture when the app stops
        camera.release()'''
    

# Function to run the second app on port 8088
def run_app2():
    app2.run(Url_Address,8088,threaded=True)
    '''try:
        app2.run(host=Url_Address, port=8088, debug=True, use_reloader=False)
    finally:
        # Release the video capture when the app stops
        camera.release()'''

if __name__ == '__main__':
    #Start each app on a separate thread
    thread1 = threading.Thread(target=run_app1)
    thread2 = threading.Thread(target=run_app2)
    
    thread1.start()
    thread2.start()
    
    thread1.join()
    thread2.join()
	
