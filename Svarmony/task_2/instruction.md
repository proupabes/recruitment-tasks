# Test Assignment

## Task 2 - Service Design

### Introduction

In this task we don't want you to hand in anything. Instead, we would like to
give you the opportunity to demonstrate your ability to think critically about
complex processes and use this as a base for a discussion in the next interview
stage. Don't worry, if you can't come up with a solution for the questions
below - we will try to find one together.

### Background

We want to publish an app that can detect snakes with a smartphone camera.

The computer vision team has developed three applications *Preclassifier*, 
*Classifier* and *Trainer* that function together as a backend. A mobile app 
is supposed to send one image (10MB each) per second to the  backend. They want 
to provide their service for up to 200 users at the same  time. The mobile app
needs to receive the result as quickly as possible.

We came up with a list of questions that we have already asked the computer 
vision team:

- Why don't you run the entire program directly on the mobile phone?
- How do we run it?
- What are the resource requirements for the components?

To which they responded,

- *Preclassifier* takes an image path of the local file system
 as input and outputs a json file. *Classifier* takes the image path plus the 
json file from *Preclassifier* and prints the result ("snake" or "no snake") to
stdout:

```
./Prelassifier --image ./dog-image.jpg --out prefilter.json
>>>Results written to prefilter.json
./Classifier --image ./dog-image.jpg --prefilter  prefilter.json
>>>no snake
```
- Running the application on the phone would drain the phone battery.
- The size of the Preclassifier and it's libraries are no more than 100MB. It
takes about 500MB of memory and one CPU to run this component.
- The size of the Classifier and it's libraries are no more than 500MB. It
takes about 4GB of memory and two CPUs to run.
- The size of the Trainer and it's libraries are no more than 1 GB. It takes
about 500MB of memory and four CPUs to run.
- The size of the snake.model is no more than 500MB.
- It takes the Trainer about 10 minutes to compute a new model file. The
Classifier must not run with a model file older than 15 min to keep up with
snake camouflage attempts.
- It takes the Preclassifier 200 ms to compute the result for a single image.
- The Preclassifier binary can only process one image at once.
- It takes Classifier 40 ms to compute the result for a single image. The Classifier
 binary can only process one image at once as well.

We think some of this information is relevant. 

### Task

Question 1. Do you have any additional question for the computer vision 
team could help us to plan the migration?

Question 2. Suppose your questions are answered to your satisfaction, 
how would you assemble these components in the cloud? 
Which tools would you use?

Bonus: The system is also supposed to be set up in private cloud that is not
connected to the internet (mobile app will send images over local network).
Let's assume that any available technology can be set up in this cloud. How
shall we proceed?

Bonus:
Let's assume that we have usage peaks (10.000 requests/s) that are going
beyond, what our system can process. How can we design it in a way that 
the service is still acceptable (200 requests/s, short latency)?

