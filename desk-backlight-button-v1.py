#!/usr/bin/python
# pylint: disable=W0312

# Simple strand test for Adafruit Dot Star RGB LED strip.
# This is a basic diagnostic tool, NOT a graphics demo...helps confirm
# correct wiring and tests each pixel's ability to display red, green
# and blue and to forward data down the line.  By limiting the number
# and color of LEDs, it's reasonably safe to power a couple meters off
# USB.  DON'T try that with other code!

import sys
sys.path.append('/home/pi/shared/deskLightingProject/dotStar/Adafruit_DotStar_Pi/')

from dotstar import Adafruit_DotStar
import RPi.GPIO as GPIO
import time
import io
import urllib2

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)


# Section to enter fun and weird color manually entered patterns to be displayed (30 LEDs Long)
PYP = [0x00FFFF, 0x00FFFF, 0x00FFFF, 0x00FFFF, 0x00FFFF, 0x00FFFF, 0x00FFFF, 0x00FFFF, 0xFFFF00, 0xFFFF00, 0xFFFF00, 0xFFFF00, 0xFFFF00, 0xFFFF00, 0xFFFF00, 0xFFFF00, 0xFFFF00, 0xFFFF00, 0xFFFF00, 0xFFFF00, 0xFFFF00, 0xFFFF00, 0x00FFFF, 0x00FFFF, 0x00FFFF, 0x00FFFF, 0x00FFFF, 0x00FFFF, 0x00FFFF, 0x00FFFF,]
CPC = [0xFF00FF, 0xFF00FF, 0xFF00FF, 0xFF00FF, 0xFF00FF, 0xFF00FF, 0xFF00FF, 0xFF00FF, 0x00FFFF, 0x00FFFF, 0x00FFFF, 0x00FFFF, 0x00FFFF, 0x00FFFF, 0x00FFFF, 0x00FFFF, 0x00FFFF, 0x00FFFF, 0x00FFFF, 0x00FFFF, 0x00FFFF, 0x00FFFF, 0xFF00FF, 0xFF00FF, 0xFF00FF, 0xFF00FF, 0xFF00FF, 0xFF00FF, 0xFF00FF, 0xFF00FF,]


# Contains all of the Information which the user sets up at beginning of setup
button_pin = 12          # BCM GPIO Pin number that the button is connected to
GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)  #Set as an input

numpixels = 30           # Number of LEDs in strip
LINK = "http://192.168.0.3:8080" # Address of the Server:8080
BRIGHTNESS = 200         # 0-255 how bright the LEDs should be 255 = 100% duty cycle

strip = Adafruit_DotStar(numpixels, 12000000)
strip.begin()            # Initialize pins for output
strip.setBrightness(BRIGHTNESS) # Limit brightness to ~1/4 duty cycle (0-255)
color = 0xFF0000         # 'On' color (starts Green)

print "Setup: ButtonPin: ", button_pin, "\nNumber of LEDs: ", numpixels 


# Enters this on Button Press. It returns how long the button was held (Waits for release).
# If the button is held for more than 3.1 seconds, stop waiting and return.
def pushAndHoldTime(pTimeStart):
    # This is an interrupt that waits for the rising edge (button released)
    # OR 3 seconds to pass to continue with the program
    if GPIO.input(button_pin,) == 1:                      # if button was released before we got to this point
        time_release = time.time()                        # take time reading of 'button release'
        return time_release-pTimeStart                    # return amount of time button was held for
    else:
        GPIO.wait_for_edge(button_pin, GPIO.RISING, timeout=3100)
        time_release = time.time()                        # Take the time of the button release
        hold_time = ("%.3f" % (time_release-pTimeStart))  # Calculate time the button was held
        print "Rising edge detected. Button held for: ", hold_time, " seconds."

        return time_release-pTimeStart                    # Return the time the button was held

# Screen Follow Mode: Sets the LEDs to mimic the monitor screen colors
def screen_follow():
    try:
        # Fade the LEDs OFF to signify we are starting screen follow mode
        fadeOff()
        first_loop = 0  # Need this to do the Fade back ON for the first loop, then will always be on

        time_auto_begin = time.time()
        holdTime = pushAndHoldTime(time_auto_begin) # Calls function which waits for button release returns time button held
        if holdTime >= 3.0:             # Button was held for more than 3 seconds
            fadeOffAndWait()
        print "Entering Screen Follow Color Mode..."

        while True:
            try:
                # Read in the information from the web server set up from the Windows PC
                # If it cannot reach the link in the timeout specified, it will return to main
                f = urllib2.urlopen(LINK, timeout=4)
            except urllib2.URLError as err:
                print err
                main()
            myfile = f.read()
            time_read = time.time()
            # Parse the data from the website into a list of strings
            values_read = myfile.split(" ")

            # Creates a 2D array to store the color values(RGB) for each LED from values_read
            color_values = []
            for i in range(0, numpixels*3, 3):
                rgb_values = [0, 0, 0]
                for rgb in range(0, 3, 1):
                    colorValue = int(filter(str.isdigit, values_read[i+rgb]))
                    rgb_values[rgb] = (colorValue)
                color_values.append(rgb_values)
            print color_values

            # Doing array conversion from decimal values in color_values to a decimal format
            # that we will be able to pass to the LED Strip.
            # NOTE: colors in color_values are RGB but the LED strip I have is GRB.
            # This is corrected in this conversion process
            color_values_shift = color_values # initialize as color values
            for i in range(0, len(color_values), 1):
                for n in range(0, 2, 1):
                    if n == 0:
                        color_values_shift[i][n] <<= 8
                    if n == 1:
                        color_values_shift[i][n] <<= 16
            for i in range(0, len(color_values_shift), 1):
                color_values_shift[i] = color_values_shift[i][0] + color_values_shift[i][1] + color_values_shift[i][2]

            print "\n", color_values_shift

            # We now have the data in a format we can use so we are able to send it to LEDs.
            flowRight_array(color_values_shift)

            # The LEDs will still be OFF if it is first time through because of fade OFF function, turn back ON
            if first_loop == 0:
                fadeOn(BRIGHTNESS)
            first_loop += 1
            # Every 0.7 seconds read the data on the server and update.
            # On button press return to main.
            print "Updating LED Values every 0.7 seconds."
            while time.time() - time_read <= 0.7:
                if GPIO.input(button_pin) == 0:
                    print "Returning to Main"
                    main()

    except KeyboardInterrupt:
        print "Program ended on Keyboard Interrupt - Have to run again for lights to respond"
        flowRight(0x000000)
        GPIO.cleanup()


# Sends out the new color to the DotStar strip where the new color is updated from left to right
# over the old color replacing it with the color passed in the parameters
def flowRight(color):
    time_start = time.time()
    head = 0                             # Index of first pixel
    while head < numpixels:
        # If a 2nd button press is detected during flowRright enter Screen Follow Mode:
        if GPIO.input(button_pin) == 0 and ("%.2f" % time.time() >= "%.2f" % (time_start + 0.2)):
            screen_follow()

        strip.setPixelColor(head, color) # Set 'head' pixel
        strip.show()                     # Refresh strip
        time.sleep(0.8 / 50)             # Pause for fade effect

        head += 1

def flowRight_array(colors):
    if type(colors) == int:
        flowRight(colors)
        return
    time_start = time.time()
    head = 0
    while head < numpixels:
        if len(colors) == numpixels:
            if GPIO.input(button_pin) == 0 and ("%.2f" % time.time() >= "%.2f" % (time_start + 0.2)):
                main()

            strip.setPixelColor(head, colors[head]) # Set 'head' pixel
            strip.show()                            # Refresh strip
            time.sleep(0.8/50)

            head += 1                               # Pause for fade effect

        else:
            print "Not correct dimmensions of array passed into flowRight"

# Function to fade the LEDs OFF and then finally turn LEDs OFF completely
def fadeOff():
    for i in range(0, BRIGHTNESS, 1):
        strip.setBrightness(BRIGHTNESS-i)
        strip.show()
        time.sleep(0.005)
    for n in range(0, numpixels, 1):
        strip.setPixelColor(n, 0x000000)
    strip.show()                      # Refresh strip
    return

# Function to fade the LEDs ON to the BRIGHTNESS specified
def fadeOn(on_brightness):
    for i in range(0, on_brightness, 1):
        strip.setBrightness(i)
        strip.show()
        time.sleep(0.005)


# Function to Fade the LEDs OFF, then wait for the next button press to turn back on at the
# defined BRIGHTNESS level at the beginning of the program
def fadeOffAndWait():
    print "Pressed for 3 seconds: Shutting OFF"
    # Output Black to all LEDs
    # for i in range(0, numpixels, 1):
    #     strip.setPixelColor(i, 0x000000) # Turn on 'head' pixel
    # strip.show()                     # Refresh strip
    fadeOff()
    # Adding interrupt to wait for the next button push
    time.sleep(3)                   # wait so button hold doesn't turn on lights again on accident
    GPIO.wait_for_edge(button_pin, GPIO.FALLING)
    strip.setBrightness(BRIGHTNESS)
    main()


#---- MAIN ----
def main():
    try:
        strip.setBrightness(BRIGHTNESS)
        color = [0xFF0000, 0xFFFF00, 0x00FF00, 0x00FFFF, 0x0000FF, 0xFF00FF, PYP, CPC] # Green, Yellow, Red, Purple, Blue, Cyan and special ones
        counter = 0
        while True:                             # Loop until Keyboard Interrupt
            holdTime = 0
            time_press = 0
            if GPIO.input(button_pin) == 0:     # if Button Pressed enter
                time_press = time.time()        # Time reading of Button Press

                holdTime = pushAndHoldTime(time_press) # Calls function which waits for button release returns time button held

                if holdTime >= 3.0:             # Button was held for more than 3 seconds
                    fadeOffAndWait()            # Turn the LEDs OFF and wait for next button press

                if counter == len(color):       # Reset counter to beginning of color[]
                    counter = 0
               
                flowRight_array(color[counter]) # Write a color change to the LEDs
                counter += 1                    # Changes from Green -> Red -> Blue

    except KeyboardInterrupt:  # On Keyboard Interrup (Ctrl-C), clean up then exit program
        print "Program ended on Keyboard Interrupt - Have to run again for lights to respond"
        flowRight(0x000000)
        GPIO.cleanup()

# Run through main infinite loop
main()

GPIO.cleanup() # At end of program cleanup the GPIO
