---
layout: page
title: Balancebot
summary: Self-balancing inverted pendulum robot, capable of autonomous or remote-controlled movement.
repo: https://github.com/chen-harrison/balancebot
---
The Balancebot project is one of three projects I took part in for the Robotic Systems Laboratory course (ROB 550) at the University of Michigan. It involved programming the functionality of a two-wheeled self-balancing robot that behaves like an inverted pendulum. The Robot Control Library (RCL) in C was used in conjunction with the Mobile Robot Cape (MRC), which was made custom and is capable of running the bot, voltage regulators, motor drivers, and IMU. This project was carried out with two other teammates, Ziyue Zhou and Yufei Zhu.


<h1 class="heading">PART 1: BALANCING</h1>

The first part of the project involved measuring and characterizing the robot in order to inform the development of the PID controllers used to keep it upright.

<h3 class="subheading">System Modeling</h3>
- ``common/mb_defs.h``: relevant parameters such as pins, chips, channels, polarities, gear ratios, resolutions, and measurements
- ``common/mb_motor.c``: functions that initalize, set velocity, and read velocity for the wheels using PWM and GPIO functions in RCL
- ``measure_moments/measure_moments.c``: functions to read and store gyroscope, accelerometer, and Euler angle data off of the IMU
  - Used data to calculate the moments of inertia about the x-, y-, and z-axes
- ``measure_motors/measure_motors.c``: functions used to calculate motor parameters like coil resistance, no load speed, motor constant, stall torque, etc.

<h3 class="subheading">Balance & Heading Controller</h3>
<p align="center">
  <img src="/assets/projects/balancebot/controller.jpg" width="640">
</p>

- ``common/mb_controller.c``: implemented two PID controllers used to balance the robot upright, and a third parallel PID controller to control direction
  - Inner loop: body angle (theta) PID controller
  - Outer loop: wheel position (phi) PID controller
  - Parallel loop: heading angle (psi) PID controller

<br>
<p align="center">
  <img src="/assets/projects/balancebot/theta.jpg" width="270">
  <img src="/assets/projects/balancebot/phi.jpg" width="270">
  <img src="/assets/projects/balancebot/psi.jpg" width="270">
</p>


<h1 class="heading">PART 2: MOTION CONTROL</h1>

With the robot able to balance, the team then moved onto adding movement functionality, as well as methods to more accurately determine its relative position.

<h3 class="subheading">Manual & Autonomous Control</h3>
- ``balancebot/balancebot.c``: manual and autonomous modes determine whether robot takes in steering inputs from controller or executes autonomous task, per competition tasks
  - Manual: increments reference wheel position and heading angle according to two directional sticks on controller
  - Autonomous: sets a destination point at the end of desired trajectory vector, then increments reference wheel position and heading angle values to travel along it

<h3 class="subheading">Odometry</h3>
<p align="center">
  <img src="/assets/projects/balancebot/odometry.jpg" width="640">
</p>

- ``common/odometry.c``: odometry functions added to locate robot based on wheel position, as read by wheel encoders
  - **Gyrodometry** algorithm corrects odometry heading angle estiamtes by monitoring large discrepancies between it and gyroscope data
  - **Kalman filter** uses odometry as the update step and gyroscope as the measurement for correction

<br>
<p align="center">
  <img src="/assets/projects/balancebot/compare.jpg" width="480">
</p>


<h1 class="heading">COMPETITION</h1>
At the end of the project period, all teams in the class pitted their robots against one another in four different events. Hence, functions that would allow the Balancebot to complete these tasks were created. Our team successfully completed all four tasks.

- ***Balancing on the Mark:*** autonomously stay balanced within 10cm of a target point for 20 seconds, and upright when external forces/disturbances are applied

- ***4x4 Left Turns:*** autonomously drive along the edges of a 1m square for four full laps while balancing and not crossing over

<p align="center">
  <img src="/assets/projects/balancebot/4x4.jpg" width="480">
</p>

- ***Straight Line Drag Racing:*** autonomously drive straight for 11m as fast as possible, stopping within a 1m stop zone at the end, and staying balanced for 5 seconds

- ***Manual Obstacle Course:*** manually steer your robot through a series of gates in two different obstacle courses, one easier and one more difficult
