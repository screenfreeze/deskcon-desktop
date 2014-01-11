DeskCon
-------

integrates your Android Device in the Desktop. Receive Notifications and Files
from your mobile Device on your Desktop PC. The Data is send via a
secure TLS Connection. The Connection is encrypted and authenticated with
self-signed Certificates (RSA-2048 PK).

Warning: This Project is still in development (beta) and may contain some Bugs or
         Security Holes. If you find any, please report them ^^
         

Information:
------------
	- http://www.screenfreeze.net/deskcon
	- Google Play Store -> DeskCon
         

Requirements (Desktop Server):
------------------------------
    - Python >= 2.7
    - pyopenssl
    - GTK3


Install:
--------
    - start deskcon.sh in Root Folder of the Project
    - (Optional) copy the Gnome Shell Extension to ~/.local/share/gnome-shell/extensions
      and activate it 
    

Usage:
------
    - start the DeskCon Desktop Server
    - start DeskCon App on your Android Device
    - select Network > Desktop Hosts
    - click the + Button and enter the IP of your Desktop PC
    - check whether the Fingerprints match


Todo:
-----
	- Unity Indicator
	- Translations
	- Mac/Windows support
	- multi File upload
	- Media Control
	- send Files to Android
	- Fingerprint validation via QR Code


Bugs:
-----
	- can't send Picasa Pictures
	- UI Design