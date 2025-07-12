import os
import sys
import urllib.request
import zipfile

def setup_tunnel():
    print("Downloading ngrok...")
    
    # Download ngrok
    url = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip"
    try:
        urllib.request.urlretrieve(url, "ngrok.zip")
        
        # Extract archive
        with zipfile.ZipFile("ngrok.zip", 'r') as zip_ref:
            zip_ref.extractall(".")
        
        # Remove archive
        os.remove("ngrok.zip")
        
        # Create batch file
        with open("start_tunnel.bat", "w", encoding='cp866') as f:
            f.write("@echo off\n")
            f.write("echo Starting tunnel...\n")
            f.write("echo Press Ctrl+C to stop\n")
            f.write("echo.\n")
            f.write("ngrok http --domain=your-domain.ngrok.app 5000\n")
        
        print("\nSetup completed!")
        print("\nInstructions:")
        print("1. Register at ngrok.com")
        print("2. Get your authtoken")
        print("3. Run: ngrok config add-authtoken YOUR_TOKEN")
        print("4. Run Flask app: python app.py")
        print("5. In another window run: start_tunnel.bat")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup_tunnel() 