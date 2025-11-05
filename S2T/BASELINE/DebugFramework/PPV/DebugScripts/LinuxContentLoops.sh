#!/bin/bash

# Prompt the user to enter the number of times to run the commands
read -p "Enter the number of iterations: " n

# Check if the input is a valid number
if ! [[ "$n" =~ ^[0-9]+$ ]]; then
    echo "Error: Please enter a valid number."
    exit 1
fi

# Read the commands from the file
commands_file="commands.txt"
if [[ ! -f "$commands_file" ]]; then
    echo "Error: Commands file '$commands_file' not found."
    exit 1
fi

# Logfile to save the console outputs
logfile="run_commands.log"

# Clear the logfile if it exists
> "$logfile"

# Loop to run the commands n times
for ((i=1; i<=n; i++))
do
    echo "Iteration $i:" | tee -a "$logfile"
    while IFS= read -r command
    do
        echo "Running: $command" | tee -a "$logfile"
        eval "$command" | tee -a "$logfile"
    done < "$commands_file"
done

echo "Completed $n iterations." | tee -a "$logfile"