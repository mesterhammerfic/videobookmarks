const youtubeVideoID = document.getElementById("yt-video-id").value
const videoID = parseInt(document.getElementById("video-id").value)
const tagListID = parseInt(document.getElementById("tag-list-id").value)
// This code loads the IFrame Player API code asynchronously.
var tag = document.createElement('script');
tag.src = "https://www.youtube.com/iframe_api";
var firstScriptTag = document.getElementsByTagName('script')[0];
firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);

// This function creates an <iframe> (and YouTube player)
//    after the API code downloads.
var player;
function onYouTubeIframeAPIReady() {
    player = new YT.Player('player', {
        videoId: youtubeVideoID,
        playerVars: {
        'playsinline': 1
        },
        events: {
        'onReady': onPlayerReady,
        }
    });
}
// 4. The API will call this function when the video player is ready.
function onPlayerReady(event) {
    refreshTagList(videoID, tagListID);
    event.target.playVideo();
}
// Function to fetch data from an endpoint with JSON body
async function fetchData(endpoint) {
    const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ videoLinks: [] })
    });
    const data = await response.json();
    return data;
}
async function refreshSuggestions(tagListId) {
    const url = `/get_tags/${tagListId}`;
    const [tagData] = await Promise.all([fetchData(url)]);
    // Clear the existing tag suggestions
    const tagSuggestions = document.getElementById('tagSuggestions');
    tagSuggestions.innerHTML = '';

    // Process the retrieved data and add tags to the tag list
    tagData.forEach(tag => {
        tagSuggestion = document.createElement('option');
        tagSuggestion.textContent = tag.tag;
        tagSuggestion.value = tag.tag;
        tagSuggestions.appendChild(tagSuggestion)
    });
}
// handle buttons and form for adding tag
const tagInput = document.getElementById('tag-input');
const addTagButton = document.getElementById('add-tag-button');

addTagButton.addEventListener('click', (event) => {
    event.preventDefault()
    const tagName = tagInput.value;
    const currentTime = player.getCurrentTime();

    // Create a new tag on the server using AJAX
    const url = '/add_tag';

    fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          yt_video_id: youtubeVideoID,
          tag_list_id: tagListID,
          tag: tagName,
          timestamp: currentTime
        })
    })
    .then(response => response.json())
    .then(() => {
      // After adding the tag, refresh the tag list
      refreshTagList(videoID, tagListID);
      refreshSuggestions(tagListID)
      tagInput.value = '';
    })
    .catch(error => {
      console.error('Error adding tag:', error);
    });
});

// create seek to function so that users can click on a timestamp
function jumptoTime(timepoint) {
    event.preventDefault();
    player.seekTo(timepoint, true);
    player.playVideo();
}

function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    const formattedTime = `${minutes}:${remainingSeconds < 10 ? '0' : ''}${remainingSeconds}`;
    return formattedTime;
}
// create a function to add tags
function addTag(tagName, time) {
    const tagList = document.getElementById('tag-list').getElementsByTagName('tbody')[0];
    const row = tagList.insertRow(-1); // Insert a row at the end of the table
    const cell1 = row.insertCell(0);
    const cell2 = row.insertCell(1);

    cell1.innerHTML = tagName;

    const timestampButton = document.createElement('button');
    timestampButton.textContent = formatTime(time);
    timestampButton.addEventListener('click', () => {
        player.seekTo(time);
    });
    cell2.appendChild(timestampButton);
}

// create request to dynamically update tag list when users updates tags
function refreshTagList(videoId, tagListId) {
    const url = `/video_tags/${videoId}/${tagListId}`;

    fetch(url)
    .then(response => response.json())
    .then(data => {
        // Clear the existing tag list (tbody)
        const tagList = document.getElementById('tag-list').getElementsByTagName('tbody')[0];
        tagList.innerHTML = '';

        // Process the retrieved data and add tags to the tag list
        data.forEach(tag => {
            addTag(tag.tag, tag.timestamp);
        });
    })
    .catch(error => {
      console.error('Error fetching tags:', error);
    });
}
refreshSuggestions(tagListID);

// add event listener for timestamp tags
const tagList = document.getElementById('tag-list');
tagList.addEventListener('click', (event) => {
    if (event.target && event.target.matches('button.timestamp')) {
        const time = parseFloat(event.target.dataset.timestamp);
        player.seekTo(time);
        }
    });