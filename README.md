# Video Bookmarks
Tag videos at specific timestamps for easy reference

## Quickstart Pre-Reqs

 - clone the repository locally
 - in the `videobookmarks` directory, 
do`python3 -m pip install .` for setup
 - export a DB_URL environment variable,
use a value with the suffix `_test` to run unit tests
 - export a YouTube API key environment as `YT_API_KEY`. Note that if the API Key has not been shared with you, 
you will need to generate one.

 Use Makefile commands below to run install dependencies and unit tests.

------------------------

### Schema
<img src="img/schema.png" alt="image" width="400" height="auto">

`user` Contains the encrypted login credentials for users.

| field    | meaning                   |
|----------|---------------------------|
| username | plain text/human readable |
| password | encrypted                 |

`tag_list` 
A tag list is a collection of related tags.
One user can create one or more tag lists. 
Each tag list is associated with only one user.

| field       | meaning                                                                                                                                                                                         |
|-------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| created     | timestamp to track when it was created                                                                                                                                                          |
| name        | name of the tag list itself. arbitrary, user defined.                                                                                                                                           |
| description | optional: description of what the tag list is tracking                                                                                                                                          |
| deleted     | boolean: true if the tag list has been deleted by the user. <br/>If true, the tag list will not show up in the app. It is kept in the database in case the original author wants to restore it. |

`video` 
The youtube video id must be added to the database in order for tags to be added to it. 
This is done automatically when the first tag is added to a video in the app.
We store some extra data here so that we don't have to continuously make calls to the youtube
API as users are navigating the app.

| field     | meaning                                           |
|-----------|---------------------------------------------------|
| link      | text: the youtube video id                        |
| thumbnail | text: a link to the youtube hosted thumbnail image |
| title     | the title of the video                            |

`tag` 
Once a tag list has been created, a user can add tags to it. 
A tag list can contain multiple tags, but a tag can only
belong to 1 tag list. A video can be linked to multiple tags, but a tag can only be linked to 1 video.

| field             | meaning                                                                                                                                                                                                                        |
|-------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| tag               | the label of the tag. Arbitrary, user defined. <br/>eg. in a youtube video of a nature documentary, a user might tag a specific timestamp with the tag "bird" to signify a  point in the video when a  bird appears on screen. |
| youtube_timestamp | integer: the time in seconds when the tag occurs in the video                                                                                                                                                                  |
| created           | timestamp to track when it was created                                                                                                                                                                       |

## ML Automated Tagging Pipeline

WIP This ML pipeline wll enable the user to submit a request for a video to be automatically tagged with ML. 
<img src="img/look-mark-predictions.png" alt="image" width="400" height="auto">

Todo:
- ~~design emotion detection algorithm (proof of concept)~~
- set up ML prediction transformation lambda that sends to look-mark
- set up emotion detection algorithm in glue with pyspark
- set up data extraction lambda (youtube video downloader)
- set up api endpoint that sends to sqs queue

### Proof of concept for emotion detection:
I set up a notebook ([here](notebooks/emotion_detection.ipynb))
and I also included a sample of the output in a csv ([here](notebooks/emotion_detection%20-%20aQoFrRq6Ds8.csv)).
This data was then uploaded to the database under my account, you can view it [here](https://look-mark.com/tagging/10/aQoFrRq6Ds8).
In production, the user will submit a youtube link, and a modified version
of the code in this notebook will be run on AWS Glue with PySpark. The results
will then be uploaded to the users account.

### ML Prediction Transformation Lambda
This is the lambda represented by step 3 in the diagram 
above. It will take the output of the emotion detection 
algorithm and transform it into a format that can be sent to the
look-mark database. The input format will be a csv with the following
columns:

| column         | meaning                                                                                                         |
|----------------|-----------------------------------------------------------------------------------------------------------------|
| frame          | integer: the frame number of the video. This is the frame number of the video that the emotion was detected in. |
| timestamp      | float: This is the timestamp in seconds of the video that the emotion was detected in.                          |
| classification | string: This is the emotion that was detected in the video. Null if no emotion was detected.                    |
| score          | float: This is the confidence score of the emotion detection. Null if no emotion was detected.                  |
| scene          | integer: The video is split into scenes, each scene is assigned an integer id.                                  |

