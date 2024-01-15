// Arrays to store selected tags and videos
const selectedTags = [];
const selectedVideos = [];
const tagListId = document.getElementById("tag-list-id").value;

function hasIntersection(arr1, arr2) {
  return arr1.some(element => arr2.includes(element));
}

// Function to fetch data from an endpoint with JSON body
async function fetchData(endpoint, body) {
    const response = await fetch(endpoint, {
        method: 'GET'
    });
    const data = await response.json();
    return data;
}

// Function to update the lists based on selected filters
async function updateLists() {
    const tagParams = { videoLinks: selectedVideos };
    const videoParams = { tags: selectedTags };

    // Fetch filtered data for tags and videos
    const [tagsData, videosData] = await Promise.all([
        fetchData(`/get_tags/${tagListId}`),
        fetchData(`/get_videos/${tagListId}`)
    ]);

    const list1Content = document.getElementById("list1-content");
    list1Content.innerHTML = ""; // Clear existing content
    var tag_buttons_enabled = [];
    var tag_buttons_disabled = [];
    tagsData.forEach(tag => {
        const tagButton = document.createElement("button");
        tagButton.label = tag.tag;
        tagButton.textContent = `${tag.tag} (${tag.count})`;
        tagButton.classList.add("button");

        // Check if the tag is in any of the selected videos
        if (selectedVideos.length != 0) {
            tagButton.disabled = !hasIntersection(selectedVideos, tag.links); // Disable button if show is false
        } else {
            tagButton.disabled = false
        }

        // Check if the tag is in the selectedTags array
        if (selectedTags.includes(tag.tag)) {
            tagButton.classList.add("selected");
        }

        // Toggle the selected state when clicked
        tagButton.addEventListener("click", () => {
            if (selectedTags.includes(tag.tag)) {
                // Deselect the tag
                const index = selectedTags.indexOf(tag.tag);
                selectedTags.splice(index, 1);
            } else {
                // Select the tag
                selectedTags.push(tag.tag);
            }

            updateLists(); // Update the lists based on selections
        });
        if (tagButton.disabled) {
            tag_buttons_disabled.push(tagButton);
        } else {
            tag_buttons_enabled.push(tagButton);
        };
        tag_buttons_enabled.forEach(button => {
            list1Content.appendChild(button);
        });
        tag_buttons_disabled.forEach(button => {
            list1Content.appendChild(button);
        })
    });

    const list2Content = document.getElementById("list2-content");
    list2Content.innerHTML = ""; // Clear existing content
    var video_buttons_enabled = [];
    var video_buttons_disabled = [];

    videosData.forEach(video => {
        const videoButton = document.createElement("button");
        videoButton.classList.add("video-item");
        videoButton.label = video.link;

        // Check if the video has in any of the selected tags
        if (selectedTags.length != 0){
            videoButton.disabled = !hasIntersection(selectedTags, video.tags); // Disable button if show is false
        } else {
            videoButton.disabled = false
        }

        // Create a link to open the video when the thumbnail is clicked
        const videoLink = document.createElement("a");
        videoLink.href = `/tagging/${tagListId}/${video.link}`;
        videoLink.classList.add("video-thumbnail-link");

        const thumbnail = document.createElement("img");
        thumbnail.src = video.thumbnail;
        thumbnail.src = video.thumbnail;
        thumbnail.classList.add("video-thumbnail");

        const videoDetails = document.createElement("div");
        videoDetails.classList.add("video-details");

        const titleElement = document.createElement("div");
        titleElement.classList.add("video-title");
        titleElement.textContent = video.title;

        const tagCountElement = document.createElement("div");
        tagCountElement.classList.add("video-tag-count");
        tagCountElement.textContent = `Number of Tags: ${video.num_tags}`;

        videoDetails.appendChild(titleElement);
        videoDetails.appendChild(tagCountElement);

        videoLink.appendChild(thumbnail);

        videoButton.appendChild(videoLink);
        videoButton.appendChild(videoDetails);

        // Check if the video is in the selectedVideos array
        if (selectedVideos.includes(video.link)) {
            videoButton.classList.add("selected");
        }

        // Toggle the selected state when clicked
        videoButton.addEventListener("click", () => {
            if (selectedVideos.includes(video.link)) {
                // Deselect the tag
                const index = selectedVideos.indexOf(video.link);
                selectedVideos.splice(index, 1);
            } else {
                // Select the tag
                selectedVideos.push(video.link);
            }

            updateLists(); // Update the lists based on selections
        });
        if (videoButton.disabled) {
            video_buttons_disabled.push(videoButton);
        } else {
            video_buttons_enabled.push(videoButton);
        };
        video_buttons_enabled.forEach(button => {
            list2Content.appendChild(button);
        });
        video_buttons_disabled.forEach(button => {
            list2Content.appendChild(button);
        })
    });
}

function youtube_parser(url){
    var regExp = /.*(?:youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=)([^#\&\?]*).*/;
    var match = url.match(regExp);
    return match&&match[1];
}

const tagVideoForm = document.getElementById("new_video_tagging");
tagVideoForm.addEventListener("submit", () => {
    const newVideoLink = document.getElementById("new_video_link").value;
    const videoIdInput = document.getElementById("new_video_id");
    videoIdInput.value = youtube_parser(newVideoLink);
});

// Initial load with no filters
updateLists();