# 🛠️ Phishing Detector Extension - Troubleshooting Guide

## ❌ "Failed to fetch" Error

If you're seeing the "Failed to fetch" error, follow these steps:

### 1. **Check if Backend is Running**
```bash
# Navigate to the project directory
cd PhishDetectorExtension

# Start the backend using the startup script
python start_backend.py
```

### 2. **Manual Backend Startup**
If the startup script doesn't work:
```bash
# Navigate to backend directory
cd backend

# Install requirements
pip install -r requirements.txt

# Start the server
python app.py
```

### 3. **Verify Backend is Working**
Open your browser and go to: `http://localhost:5000/health`

You should see: `{"status": "Phishing detection backend running ✅"}`

### 4. **Check Extension Permissions**
1. Open Chrome Extensions page (`chrome://extensions/`)
2. Find "Phishing Shield" extension
3. Make sure it's enabled
4. Check that it has the required permissions

### 5. **Common Issues & Solutions**

#### **Port 5000 Already in Use**
```bash
# Find what's using port 5000
netstat -ano | findstr :5000

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F
```

#### **Python/Flask Not Found**
```bash
# Install Python dependencies
pip install flask flask-cors pandas scikit-learn requests beautifulsoup4 lxml whois

# Or use the requirements file
pip install -r backend/requirements.txt
```

#### **CORS Issues**
The extension is configured to handle CORS properly, but if you still have issues:
1. Make sure the backend is running on `localhost:5000`
2. Check that the extension has the correct host permissions in `manifest.json`

#### **Extension Not Loading**
1. Reload the extension in Chrome Extensions page
2. Check the browser console for errors
3. Make sure the extension files are in the correct directory structure

### 6. **Testing the Connection**

#### **Test Backend Health**
```bash
curl http://localhost:5000/health
```

#### **Test Phishing Detection**
```bash
curl -X POST http://localhost:5000/check \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.google.com"}'
```

### 7. **Extension Console Debugging**

1. Open Chrome DevTools (F12)
2. Go to Console tab
3. Look for error messages
4. Check the Network tab for failed requests

### 8. **Backend Console Debugging**

When running the backend, you should see:
```
✅ Model loaded successfully!
✅ Advanced category model loaded successfully!
* Running on all addresses (0.0.0.0)
* Running on http://127.0.0.1:5000
* Running on http://[::1]:5000
```

### 9. **Quick Fixes**

#### **Restart Everything**
1. Stop the backend (Ctrl+C)
2. Reload the extension in Chrome
3. Start the backend again
4. Test with a website

#### **Clear Extension Data**
1. Go to `chrome://extensions/`
2. Find "Phishing Shield"
3. Click "Remove"
4. Reload the extension folder

#### **Check Firewall/Antivirus**
- Make sure Windows Firewall isn't blocking the connection
- Check if antivirus is interfering with the extension

### 10. **Still Having Issues?**

If you're still experiencing problems:

1. **Check the logs:**
   - Backend console output
   - Chrome extension console
   - Browser network tab

2. **Verify the setup:**
   - Python 3.7+ installed
   - All dependencies installed
   - Backend running on port 5000
   - Extension loaded and enabled

3. **Test with a simple URL:**
   - Try `https://www.google.com`
   - Check if the popup appears
   - Look for any error messages

### 🎯 **Success Indicators**

When everything is working correctly, you should see:
- ✅ Backend starts without errors
- ✅ Extension loads without errors
- ✅ Popup appears when visiting websites
- ✅ Category detection works
- ✅ No "Failed to fetch" errors in console

### 📞 **Need More Help?**

If you're still having issues:
1. Check the browser console for specific error messages
2. Verify all files are in the correct locations
3. Make sure you're using the latest version of Chrome
4. Try restarting your browser and computer
