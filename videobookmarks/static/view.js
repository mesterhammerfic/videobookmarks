// Arrays to store selected tags and videos
const selectedTags = [];
const selectedVideos = [];

// Function to fetch data from an endpoint with JSON body
async function fetchData(endpoint, body) {
    const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(body)
    });
    const data = await response.json();
    return data;
}

// Function to update the lists based on selected filters
async function updateLists() {
    const tagListId = document.getElementById("tag-list-id").value;
    const tagParams = { videoLinks: selectedVideos };
    const videoParams = { tags: selectedTags };

    // Fetch filtered data for tags and videos
    const [tagsData, videosData] = await Promise.all([
        fetchData(`/get_tags/${tagListId}`, tagParams),
        fetchData(`/get_videos/${tagListId}`, videoParams)
    ]);

    const list1Content = document.getElementById("list1-content");
    list1Content.innerHTML = ""; // Clear existing content

    tagsData.forEach(tag => {
        const tagButton = document.createElement("button");
        tagButton.label = tag.tag;
        tagButton.textContent = `${tag.tag} (${tag.count})`;
        tagButton.classList.add("button");
        tagButton.disabled = !tag.show; // Disable button if show is false

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

        list1Content.appendChild(tagButton);
    });

    const list2Content = document.getElementById("list2-content");
    list2Content.innerHTML = ""; // Clear existing content

    videosData.forEach(video => {
        const videoButton = document.createElement("button");
        videoButton.classList.add("video-item");
        videoButton.disabled = !video.show; // Disable button if show is false
        videoButton.label = video.link;

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
        list2Content.appendChild(videoButton);
    });
}

// Initial load with no filters
updateLists();