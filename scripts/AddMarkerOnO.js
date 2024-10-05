// Add to custom javascript

const GRAPHQL_ENDPOINT = 'YOUR ENDPOINT HERE';
const PRIMARY_TAG_ID = String("THE TAG ID TO ASSIGN TO O-COUNTER");

function timestampToSeconds(timestamp) {
    const parts = timestamp.split(':').reverse();
    let seconds = 0;
    if (parts[0]) seconds += parseInt(parts[0], 10);
    if (parts[1]) seconds += parseInt(parts[1], 10) * 60;
    if (parts[2]) seconds += parseInt(parts[2], 10) * 3600;
    return seconds;
}

async function createSceneMarker(sceneId, timestamp) {
    const seconds = timestampToSeconds(timestamp);
    const payload = {
        "operationName": "SceneMarkerCreate",
        "variables": {
            "tag_ids": [],
            "scene_id": sceneId.toString(),
            "title": "",
            "seconds": seconds,
            "primary_tag_id": PRIMARY_TAG_ID
        },
        "query": `mutation SceneMarkerCreate($title: String!, $seconds: Float!, $scene_id: ID!, $primary_tag_id: ID!, $tag_ids: [ID!] = []) {
            sceneMarkerCreate(
                input: {title: $title, seconds: $seconds, scene_id: $scene_id, primary_tag_id: $primary_tag_id, tag_ids: $tag_ids}
            ) {
                id
            }
        }`
    };
    
    const response = await fetch(GRAPHQL_ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });

    if (!response.ok) {
        const error = await response.json();
        console.error("Error creating scene marker:", error);
    } else {
        const result = await response.json();
        console.log("Scene Marker Created:", result);
    }
}

(function() {
    const originalFetch = window.fetch;
    window.fetch = async function(...args) {
        const [resource, config] = args;

        if (resource.includes(GRAPHQL_ENDPOINT) && config && config.body) {
            try {
                const body = JSON.parse(config.body);
                if (body.operationName === "SceneAddO") {
                    const timestampElement = document.querySelector('.vjs-current-time-display');
                    let timestamp = "0:00";
                    if (timestampElement) timestamp = timestampElement.textContent.trim();

                    const confirmation = confirm(`Create Marker at timestamp ${timestamp}?`);
                    if (confirmation) {
                        const sceneId = body.variables.id;
                        createSceneMarker(sceneId, timestamp);
                    }
                }
            } catch (e) {
                console.error("Error parsing fetch request body:", e);
            }
        }

        return originalFetch.apply(this, args);
    };
})();

(function() {
    const originalOpen = XMLHttpRequest.prototype.open;
    const originalSend = XMLHttpRequest.prototype.send;

    XMLHttpRequest.prototype.open = function(method, url, async, user, password) {
        this._url = url;
        return originalOpen.apply(this, arguments);
    };

    XMLHttpRequest.prototype.send = function(body) {
        if (this._url.includes(GRAPHQL_ENDPOINT) && body) {
            try {
                const parsedBody = JSON.parse(body);
                if (parsedBody.operationName === "SceneAddO") {
                    const timestampElement = document.querySelector('.vjs-current-time-display');
                    let timestamp = "0:00";
                    if (timestampElement) timestamp = timestampElement.textContent.trim();

                    const confirmation = confirm(`Create Marker at timestamp ${timestamp}?`);
                    if (confirmation) {
                        const sceneId = parsedBody.variables.id;
                        createSceneMarker(sceneId, timestamp);
                    }
                }
            } catch (e) {
                console.error("Error parsing XMLHttpRequest body:", e);
            }
        }
        return originalSend.apply(this, arguments);
    };
})();
