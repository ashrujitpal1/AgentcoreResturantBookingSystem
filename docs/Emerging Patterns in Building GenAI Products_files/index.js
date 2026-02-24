    var data = {
        x: embeddings_3d.map(e => e[0]),
        y: embeddings_3d.map(e => e[1]),
        z: embeddings_3d.map(e => e[2]),
        customdata:customdata,
        marker: {
                size: 6,
                color:colors,
                opacity: 0.8
            },
        type: 'scatter3d',
        mode: 'markers'
    };
    var layout = {
        width: 700,
        height: 700
    };

    Plotly.newPlot('scatter-plot-3d', [data], layout);
    
    var chartElement = document.getElementById('scatter-plot-3d');

    function displayImage(imagePath) {{
            var imageElement = document.getElementById('image-display');
            var placeholderText = document.getElementById('placeholder-text');
            imageElement.src = imagePath;
            imageElement.style.display = 'block';
            placeholderText.style.display = 'none';
    }}

    chartElement.on('plotly_click', function(data) {{
        var customdata = data.points[0].customdata;
        displayImage(customdata);
    }});
    
