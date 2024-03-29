import boto3
import pandas as pd
import os
import psycopg2


DB_URL = os.getenv('DB_URL')
if DB_URL is None:
    raise ValueError(
        "Missing DB_URL environment variable, could not connect to Database"
    )


def transform_emotion_data(df):
    # the minimum score needed for an emotion to be used
    minimum_score = .8
    exclude_neutral_min_score = .96
    df["emotion"] = df.apply(lambda x: "no_emotion" if x["score"] < minimum_score else x["emotion"], axis=1)
    df["emotion"] = df.apply(
        lambda x: "no_emotion" if x["emotion"] == "neutral" and x["score"] < exclude_neutral_min_score else x[
            "emotion"],
        axis=1
    )
    # how many images to consider at a time when deciding if an emotion shift
    steps = 3

    def most_common_tag_and_frame(list_of_rows):
        """
        Detect the most common emotion that was detected in a collection of images
        and the frame that this emotion occurs on first
        Returns None if there is a tie or if all of the rows are labeled "no_emotion"
        """
        tags = []
        for r in list_of_rows:
            if r["emotion"] != "no_emotion":
                tags.append(r["emotion"])
        if not tags:
            return None
        counts = {tag: tags.count(tag) for tag in tags}
        if len(set(tags)) > 1 and len(set(counts.values())) == 1:
            return None
        most_common = max(set(tags), key=counts.get)
        for row in list_of_rows:
            if row["emotion"] == most_common:
                return most_common, row["frame"]

    def get_emotion_shifts(dataframe_of_scenes):
        """
        returns a list of frames that indicate when the emotion shifted
        """
        rows = []
        for i, r in dataframe_of_scenes.iterrows():
            rows.append(r)
        if len(dataframe_of_scenes) < steps:
            frame = most_common_tag_and_frame(rows)[1]
            return [frame, ]

        output_list = []
        i = 0
        last_emotion = None
        while i + steps <= len(rows):
            most_common = most_common_tag_and_frame(rows[i:i + steps])
            if most_common is not None:
                current_emotion = most_common[0]
                frame = most_common[1]
                if last_emotion != current_emotion:
                    last_emotion = current_emotion
                    output_list.append(frame)
            i += 1
        return output_list

    emotion_shifts = []
    for scene in df["scene"].unique():
        scene_df = df[df["scene"] == scene]
        if len(scene_df):
            emotion_shifts.extend(
                get_emotion_shifts(scene_df),
            )

    df["emotion_shift"] = df["frame"].map(lambda x: x in emotion_shifts)
    return df


# this function takes in the dataframe and uploads it to the database
# it also takes in the user_id and the tag_list_id from the event
def upload_to_db(df, user_id, tag_list_id, video_id):
    # Connect to the database
    connection = psycopg2.connect(DB_URL)
    cursor = connection.cursor()
    for index, row in df[(df["emotion_shift"] == True) & (df.emotion != "no_emotion")].iterrows():
        # for each row, we are going to insert a tag into the tag table.
        cursor.execute(
            "INSERT INTO tag (user_id, tag_list_id, video_id, youtube_timestamp, tag) VALUES (%s, %s, %s, %s, %s)",
            (user_id, tag_list_id, video_id, row["timestamp"], row["emotion"]),
        )


def lambda_handler(event, context):
    filename = event['filename']
    s3 = boto3.resource('s3')
    obj = s3.Object('ml-pipeline-bucket', filename)
    response = obj.get()
    # Load the parquet file into a pandas dataframe
    df = pd.read_parquet(response['Body'])
    df = transform_emotion_data(df)
    # get the user_id and the tag_list_id from the event
    user_id = event['user_id']
    tag_list_id = event['tag_list_id']
    video_id = event['video_id']
    upload_to_db(df, user_id, tag_list_id, video_id)

