function make_timeline(element, headspace, xtics, xlabels, weekly_data) {
    var headspace = headspace;
    var svg = d3.select(element);

    /** Add frame around graph */      
    var svg_frame = svg.select("g.frame");

    /* Add ticks to x axis */
    var line_xtics = svg_frame.selectAll('line.xtic').data(xtics);
    line_xtics.enter().append('line')
              .attr("x1", function(d) { return d.x1; })
              .attr("x2", function(d) { return d.x2; })
              .attr("y1", function(d) { return d.y1; })
              .attr("y2", function(d) { return d.y2; })
              .attr("class", function(d) { return "xtic " + d.class; });
    
    /* Add labels to x axis */
    var text_xlabels = svg.selectAll('text.xlabel').data(xlabels);
    text_xlabels.enter().append('text')
                .attr("x", function(d) { return d.x; })
                .attr("y", function(d) { return d.y; })
                .html(function(d) { return d.text })
                .attr("class", function(d) { return "xlabel " + d.class; });

    /** Add weekly data bars */
    var svg_bars = svg.select("g.inner");

    var weekly_max = d3.max(weekly_data, function(d) { return d.y });

    var rectangle_hidden = svg_bars.selectAll("rect.bar_hidden").data(weekly_data);
    var rectangle = svg_bars.selectAll("rect.bar").data(weekly_data);
    var rectangle_tex = svg_bars.selectAll("text.bar").data(weekly_data);

    var max_x = 1.0; // d3.max(weekly_data, function(d) { return d.x2 })
    var min_x = 0.0; // d3.min(weekly_data, function(d) { return d.x1 })

    function norm(x) {
        return (x - min_x) / (max_x - min_x)
    }

    function norm_delta(x) {
        return x / (max_x - min_x)
    }

    rectangle.enter().append("rect")
          .attr("x", function(d) { return (norm(d.x1)*90 + 5) + "%"; })
          .attr("y", function(d) { return headspace - (d.y / weekly_max * 50 + 5); })
          .attr("width", function(d) { return (norm_delta(d.x2 - d.x1)*90) + "%"; })
          .attr("height", function(d) { return (d.y / weekly_max * 50 + 5); })
          .attr("class", "bar");

    rectangle.enter().append("text")
          .attr("x", function(d) { return (norm((d.x1 + d.x2)/2)*90.0 + 5) + "%"; })
          .attr("y", function(d) { return headspace - (d.y / weekly_max * 50) - 10; })
          .html(function(d) { return d.y })
          .attr("id", function(d,i) { return "text-bar-" + i; })
          .attr("class", "bar");

    rectangle_hidden.enter().append("rect")
          .attr("x", function(d) { return (norm(d.x1)*90 + 5) + "%"; })
          .attr("y", function(d) { return 0; })
          .attr("width", function(d) { return (norm_delta(d.x2 - d.x1)*90) + "%"; })
          .attr("height", function(d) { return headspace; })
          .attr("class", "bar_hidden")
          .on("mouseover", function(d,i) { $("svg.timeline text#text-bar-"+i).attr("class", "bar bar_highlight"); }) /* JQuery can't set classes on SVG */
          .on("mouseout", function(d,i) { $("svg.timeline text#text-bar-"+i).attr("class", "bar"); });
}

function make_timeline_line(element, data, xlabel, ylabel) {
    // Set the dimensions of the canvas / graph
    var margin = {top: 20, right: 20, bottom: 50, left: 70}
    var width = $(element).width() - margin.left - margin.right
    var height = $(element).height() - margin.top - margin.bottom

    // Parse the date / time
    var parseDate = d3.time.format("%Y-%m-%d").parse;

    // Set the ranges
    var x = d3.time.scale().range([0, width]);
    var y = d3.scale.linear().range([height, 0]);

    // Define the axes
    var xAxis = d3.svg.axis().scale(x)
        .orient("bottom").ticks(5);

    var yAxis = d3.svg.axis().scale(y)
        .orient("left").ticks(5);

    data.forEach(function(d) {
        d.date = parseDate(d.date);
        d.value = +d.value;
    });

    data.sort(function(a,b) { return d3.ascending(a.date,b.date); });

    console.log(data)

    // Define the line
    var valueline = d3.svg.line()
        .x(function(d) { return x(d.date); })
        .y(function(d) { return y(d.value); });
        
    // Adds the svg canvas
    var svg = d3.select(element)
        .append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
        .append("g")
            .attr("transform", 
                  "translate(" + margin.left + "," + margin.top + ")");

    // Scale the range of the data
    x.domain(d3.extent(data, function(d) { return d.date; }));
    y.domain([0, d3.max(data, function(d) { return d.value; })]);

    // Add the valueline path.
    svg.append("path")
        .attr("class", "line")
        .attr("d", valueline(data));

    // Add the X Axis
    svg.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + height + ")")
        .call(xAxis);

    // Add the Y Axis
    svg.append("g")
        .attr("class", "y axis")
        .call(yAxis);

    // X axis label
    svg.append("text")
        .attr("x", width / 2)
        .attr("y", height + margin.bottom / 2)
        .attr("dy", "1em")
        .style("text-anchor", "middle")
        .text(xlabel);

    // Y axis label
    svg.append("text")
        .attr("transform", "rotate(-90)")
        .attr("y", - margin.left)
        .attr("x", - (height / 2))
        .attr("dy", "1em")
        .style("text-anchor", "middle")
        .text(ylabel);
}

