# Test Assignment

## Task 1 - Microservice Probing

### Background

One of our developers created a microservice that was supposed to have the 
following properties:

- Has REST endpoint: `/short/<ARG>`.
- <ARG> can be any combination of exactly two alphanumeric characters, e.g.: 
    "Ab", "12", "a2".
- Returns json with 'uid' key and value of exactly 32 alphanumeric characters, 
    e.g.: `{"uid":"855f938d67b52b5a7eb124320a21a139"}`.
- Is available on: <https://ionaapp.com/assignment-magic/dk/short>.

We manually checked it for one possible input parameter by visiting:
 <https://ionaapp.com/assignment-magic/dk/short/ab>.

Unfortunately the developer is on vacation and did not provide us with any 
automated tests for the microservice.

### Task

1. Write a test application that checks whether the service fulfills the
requirements (see above).
2. Wrap the application in an oci container, i.e. provide a Dockerfile.

Please provide us with the code and thoughts you have. Don't worry in case the 
task is not complete - just provide us with your considerations and describe 
how you would solve it.

Bonus: Do the same for the `long/` endpoint, that takes an argument that 
consists out of exactly three alphanumeric characters, 
e.g. <https://ionaapp.com/assignment-magic/dk/long/ab2>.

