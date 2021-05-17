# Music Subscription Application using Flask and AWS services

Services Used: 
1. AWS EC2
2. AWS S3
3. AWS DynamoDB

Step by step guide on how to deploy it on EC2 instance is mentioned in command.txt file.


Image 1 : User can Register as a new User or can Login with email id and password. 
(Username, emailID should be unique)

![Login/Register](/Capture/Capture1.PNG)


Image 2: User can Search for different music from created DynamoDB database of music.
(Serach with Song Title and/or Year and/or Artist. Use Query button to start search)

![Browse Music](/Capture/Capture2.PNG)

Image 3: User can Subscribe to any of the searched music and it will appear in his home screen. User can Unsubscribe it from the home screen

![User Home](/Capture/Capture3.PNG)
