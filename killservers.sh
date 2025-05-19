#!/bin/bash

# Colors for better readability
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Define ports commonly used by the application
NEXTJS_PORT=3000
FASTAPI_PORT=8000
ALL_PORTS="$NEXTJS_PORT $FASTAPI_PORT"

echo -e "${BLUE}=== Checking for running servers before cleanup ===${NC}"
echo "Showing processes listening on ports $ALL_PORTS:"
echo

# Display processes using lsof (better than ps for showing ports)
for PORT in $ALL_PORTS; do
  PROCESSES=$(lsof -i :$PORT -sTCP:LISTEN)
  if [ -n "$PROCESSES" ]; then
    echo -e "${GREEN}Found processes on port $PORT:${NC}"
    echo "$PROCESSES"
  else
    echo -e "${RED}No processes found on port $PORT${NC}"
  fi
done

echo -e "\n${BLUE}=== Killing development servers ===${NC}"

# Kill processes by port
killed_count=0
for PORT in $ALL_PORTS; do
  PIDS=$(lsof -ti :$PORT -sTCP:LISTEN)
  if [ -n "$PIDS" ]; then
    echo -e "${RED}Killing processes on port $PORT: $PIDS${NC}"
    kill -9 $PIDS 2>/dev/null
    let killed_count+=1
  else
    echo -e "No processes to kill on port $PORT"
  fi
done

if [ $killed_count -eq 0 ]; then
  echo -e "${GREEN}No servers were running on the specified ports.${NC}"
else
  echo -e "${GREEN}Successfully terminated $killed_count server processes.${NC}"
fi

# Wait a moment for processes to fully terminate
sleep 1

echo -e "\n${BLUE}=== Checking for running servers after cleanup ===${NC}"
echo "Showing processes listening on ports $ALL_PORTS:"
echo

# Check again to confirm processes are killed
active_count=0
for PORT in $ALL_PORTS; do
  PROCESSES=$(lsof -i :$PORT -sTCP:LISTEN)
  if [ -n "$PROCESSES" ]; then
    echo -e "${RED}WARNING: Processes still running on port $PORT:${NC}"
    echo "$PROCESSES"
    let active_count+=1
  else
    echo -e "${GREEN}Port $PORT is clear${NC}"
  fi
done

if [ $active_count -eq 0 ]; then
  echo -e "\n${GREEN}All development server ports are now free. You can start your servers.${NC}"
else
  echo -e "\n${RED}WARNING: Some processes could not be terminated.${NC}"
  echo "You might need to manually kill them or investigate further."
fi

exit 0 