# SnapClass
SnapClass is an advanced on-device edge AI solution designed for low-connectivity, high-density classroom environments. Powered by Snapdragon’s Hexagon NPU, it runs open-source large language models (LLMs), image captioning, and audio transcription entirely offline. SnapClass automates personalized learning by transcribing lectures, analyzing textbook content, and generating adaptive quizzes—bridging educational gaps in underserved regions where internet access and qualified educators are limited.

## App architecture
![Snapclass](https://github.com/user-attachments/assets/ac08564f-5530-4e68-8d1f-83d595009ebf)

### Models
- **Whisper-small (242M params)** via "openai/whisper-small"
- **nougat-small (247M params)** via "facebook/nougat-small"
- **blip-image-captioning-base** via "Salesforce/blip-image-captioning-base" running parallelly with whisper-small
- **Phi-3.5-mini-instruct (3.82B params)** via "AnythingLLM" running locally via ONNX accelerated by Snapdragon's X Elite's NPU

## Features
- 🖼Teacher dashboard with file upload and analytics view  
- Lecture and textbook PDF/audio upload  
- AI-based question and answer evaluation
- Uses Both CPU and NPU for faster on-device processing
- Identifies weak syllabus topics per student or group  
- Fully functional offline – no internet needed  
- Lightweight and fast inference using sentence embeddings

## Setup & Usage
### Step 1: Setup Local Hotspot (No Internet)
We use [MyPublicWifi](https://mypublicwifi.com/publicwifi/en/index.html) to create a local area dead network
1. Download and Install MyPublicWifi.
2. Open the app, set:
   - Network Access = No Internet Sharing
   - Turn on hotspot
3. Note the IP address shown in the app. This IP will be used to access the server from other devices.

### Step 2:Install Python Dependencies
1. Clone this repository
```
git clone https://github.com/Abbilaash/SnapClass.git
cd SnapClass
```
2. Install requirements
```
pip install -r requirements.txt
```
Install [AnythingLLM](https://anythingllm.com/) and activate AnythingLLM NPU to process LLM models in Qualcomm Hexagon NPU.
Download ```Phi 3.5 Mini Instruct 4K 2.00GB``` model.
Get you AnythingLLM Developer API from Settings>Tools>Developer API>Generate New API Key and get you workspace slug.
Replace you API key in ```server/config.yaml``` as ```api_key: <API>``` and ```workspace_slug: <my-workspace>```

### Step 3: Start the server
```
cd server
python app.py
```
Once started, the server runs locally on port ```5000```

## Access the Web Interface
- Teacher Dashboard (same server device)
```http://127.0.0.1:5000/admin```
Use the IP address shown in MyPublicWifi ad access the students portal
- Student Test Page
```http://<IP>:5000/test```
Replace <IP> with the one shown in the MyPublicWifi app after enabling the hotspot

## Screenshots
![image](https://github.com/user-attachments/assets/2f0fbba2-778e-490e-9729-7f1ab84d76c3)
![image](https://github.com/user-attachments/assets/62445589-c787-4bc3-8acb-37f5ef56ddb2)
![image](https://github.com/user-attachments/assets/352be7fd-1a9b-4709-97a6-7c6561eddf70)
![image](https://github.com/user-attachments/assets/9de25358-9031-4660-be61-b9d5e269e2fd)

## Authors
[A T Abbilaash](https://github.com/Abbilaash) - 23n201@psgtech.ac.in 
<br/>
[Nivashini N](https://github.com/nivashini2505) - 23n234@psgtech.ac.in
