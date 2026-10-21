#!/bin/bash
# Opens the local offline app; no server or runtime required.
aa_app_dir="$(cd -- "$(dirname -- "$0")" && pwd)"
if [ -d "/Applications/Google Chrome.app" ] || [ -d "$HOME/Applications/Google Chrome.app" ]; then
  open -a "Google Chrome" "$aa_app_dir/AA Controller.html"
elif [ -d "/Applications/Microsoft Edge.app" ]; then
  open -a "Microsoft Edge" "$aa_app_dir/AA Controller.html"
else
  osascript -e 'display dialog "Install Google Chrome, then open AA Controller.html with Chrome. Safari cannot connect to the Arduino." buttons {"OK"} default button "OK"'
fi
