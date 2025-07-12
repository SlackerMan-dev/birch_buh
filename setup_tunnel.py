import os
import sys
import urllib.request
import platform

def setup_tunnel():
    print("Ustanovka tunnelya...")
    
    # Opredelyaem arhitekturu sistemy
    if platform.machine().endswith('64'):
        url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
    else:
        url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-386.exe"
    
    try:
        # Skachivanie cloudflared
        print("Zagruzka cloudflared...")
        urllib.request.urlretrieve(url, "cloudflared.exe")
        print("Cloudflared uspeshno zagruzhen")
        
        # Sozdaem bat-file dlya zapuska
        bat_content = """@echo off
echo Zapusk tunnelya...
echo Dlya ostanovki nazhmite Ctrl+C
echo.
cloudflared.exe tunnel --url http://localhost:5000
"""
        
        # Zapisyvaem v file
        with open("start_tunnel.bat", "w") as f:
            f.write(bat_content)
        
        print("\nNastroyka zavershena!")
        print("\nInstruktsiya:")
        print("1. Zapustite prilozhenie: python app.py")
        print("2. V drugom okne zapustite: start_tunnel.bat")
        print("3. Skopiruyte URL iz konsoli")
        print("\nVazhno: Ne zakryvayte okno s tunnelem!")
        
    except Exception as e:
        print(f"Oshibka: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup_tunnel() 