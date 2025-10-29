from config import documents_directory

def get_video_link(context):
    if not context:
        return ""
    # We only take the link from the first document (in case there are more than one)
    document = context[0]
    file_source = document.metadata["source"]
    # Takes the video id from the name of the file
    video_id = file_source.strip(documents_directory).split('_')[0]
    video_url = "https://www.youtube.com/watch?v="+video_id
    return video_url