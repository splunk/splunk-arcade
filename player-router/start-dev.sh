#!/bin/bash

COLOR_RED="\033[0;31m"
COLOR_CYAN="\033[0;36m"
COLOR_RESET="\033[0m"

RUN_CMD="go run main.go"

go mod download

echo -e "${COLOR_RED}
  _____ ____  _      __ __  ____   __  _       ____  ____      __   ____  ___      ___
 / ___/|    \| |    |  |  ||    \ |  |/ ]     /    ||    \    /  ] /    ||   \    /  _]
(   \_ |  o  ) |    |  |  ||  _  ||  ' /     |  o  ||  D  )  /  / |  o  ||    \  /  [_
 \__  ||   _/| |___ |  |  ||  |  ||    \     |     ||    /  /  /  |     ||  D  ||    _]
 /  \ ||  |  |     ||  :  ||  |  ||     \    |  _  ||    \ /   \_ |  _  ||     ||   [_
 \    ||  |  |     ||     ||  |  ||  .  |    |  |  ||  .  \\     ||  |  ||     ||     |
  \___||__|  |_____| \__,_||__|__||__|\_|    |__|__||__|\_| \____||__|__||_____||_____|

${COLOR_RESET}

To run: ${COLOR_CYAN}${RUN_CMD}${COLOR_RESET}

"

export HISTFILE=/tmp/.bash_history
history -s "$RUN_CMD"
history -a

bash