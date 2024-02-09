import boto3
import pandas as pd

def lambda_handler(event, context):
    # Load the filename of the prediction parquet found in the s3 bucket
    filename = event['filename']
    # Load the parquet file from the s3 bucket called ml_pipeline_bucket
    s3 = boto3.resource('s3')
    obj = s3.Object('ml-pipeline-bucket', filename)
    response = obj.get()
    # Load the parquet file into a pandas dataframe
    df = pd.read_parquet(response['Body'])
    # Transform the data
    df["score"] = df["score"].fillna(0)

    df["emotion"] = df.apply(lambda x: "no_emotion" if x["score"] < minimum_score else x["emotion"], axis=1)
    df["emotion"] = df.apply(
        lambda x: "no_emotion" if x["emotion"] == "neutral" and x["score"] < exclude_neutral_min_score else x[
            "emotion"],
        axis=1
    )
