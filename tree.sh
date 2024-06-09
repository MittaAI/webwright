#!/bin/bash

# Function to display the current directory structure
display_tree() {
    clear
    find . -maxdepth 1
}

# Infinite loop to display the directory structure every 5 seconds
while true; do
    display_tree
    sleep 5
done
