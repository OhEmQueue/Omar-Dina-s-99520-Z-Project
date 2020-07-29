import requests
import json
from tqdm import tqdm

#class where each YouTube channel becomes an object
class YouTubestatistics:
    def __init__(self, api_key, channel_id):
        self.api_key = api_key
        self.channel_id = channel_id
        self.channel_statistics = None
        self.video_stats = None
        
    #collect basic stats about a channel
    def get_channel_stats(self):
        url = f'https://www.googleapis.com/youtube/v3/channels?part=statistics&id={self.channel_id}&key={self.api_key}'
        json_url = requests.get(url)
        data = json.loads(json_url.text)
        try:
            data = data["items"][0]["statistics"]
        except:
            data = None

        self.channel_statistics = data
        return data

    #collect channel video's data
    def get_channelvideo_data(self):
        channel_videos = self.get_channelvideos(limit=50)
        print(channel_videos)
        print (len(channel_videos))

        parts = ["snippet", "statistics", "contentDetails"]
        for video_id in tqdm(channel_videos):
            for part in parts:
                data = self.get_videodata(video_id, part)
                channel_videos[video_id].update(data)

        self.video_stats = channel_videos
        return channel_videos

    #get the data surrounding a video
    def get_videodata(self, video_id, part):
        url = f"https://www.googleapis.com/youtube/v3/videos?part={part}&id={video_id}&key={self.api_key}"
        json_url = requests.get(url)
        data = json.loads(json_url.text)
        try:
            data = data['items'][0][part]
        except:
            print("Error")
            data = dict()

        return data

    #get a video from a channel
    def get_channelvideos(self, limit=None):
        url = f"https://www.googleapis.com/youtube/v3/search?key={self.api_key}&channelId={self.channel_id}&part=id&order=date"
        if limit is not None and isinstance(limit, int):
            url += "&maxResults=" + str(limit)

        videos, nextpagetoken = self.get_allchannelvideos(url)
        index = 0
        while(nextpagetoken is not None and index < 10):
            nexturl = url + "&pageToken=" + nextpagetoken
            nextvideos, nextpagetoken = self.get_allchannelvideos(nexturl)
            videos.update(nextvideos)
            index += 1

        return videos

    #get all videos from a given YouTube channel
    def get_allchannelvideos(self, url):
        json_url = requests.get(url)

        data = json.loads(json_url.text)
        channelvideos = dict()
        if 'items' not in data:
            return channelvideos, None

        itemdata = data['items']
        nextpagetoken = data.get("nextPageToken", None)
        for item in itemdata:
            try:
                kind = item['id']['kind']
                if kind == 'youtube#video':
                    video_id = item['id']['videoId']
                    channelvideos[video_id] = dict()
            except KeyError:
                print("error")

        return channelvideos, nextpagetoken

    #write all collected data from the YouTube channel/videos into a json file
    def dump(self):
        if self.channel_statistics is None or self.video_stats is None:
            print("No data (none)")
            return

        fuseddata = {self.channel_id: {"channel_statistics": self.channel_statistics, "video_stats": self.video_stats}}

        channel_title = self.video_stats.popitem()[1].get('channelTitle', self.channel_id)
        channel_title = channel_title.replace(" ", "_").lower()
        file_name = channel_title + '.json'
        with open(file_name, 'w') as f:
            json.dump(fuseddata, f, indent=4)

        print('File has been dumped')
