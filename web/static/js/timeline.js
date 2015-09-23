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

    rectangle.enter().append("rect")
          .attr("x", function(d) { return (d.x1*90 + 5) + "%"; })
          .attr("y", function(d) { return headspace - (d.y / weekly_max * 50 + 5); })
          .attr("width", function(d) { return ((d.x2 - d.x1)*90) + "%"; })
          .attr("height", function(d) { return (d.y / weekly_max * 50 + 5); })
          .attr("class", "bar");

    rectangle.enter().append("text")
          .attr("x", function(d) { return ((d.x1 + d.x2)/2*90 + 5) + "%"; })
          .attr("y", function(d) { return headspace - (d.y / weekly_max * 50) - 10; })
          /*.attr("fill-opacity", function(d) { return d.y/weekly_max*0.9 + 0.1 ;})*/
          .html(function(d) { return d.y })
          .attr("id", function(d,i) { return "text-bar-" + i; })
          .attr("class", "bar");

    rectangle_hidden.enter().append("rect")
          .attr("x", function(d) { return (d.x1*90 + 5) + "%"; })
          .attr("y", function(d) { return 0; })
          .attr("width", function(d) { return ((d.x2 - d.x1)*90) + "%"; })
          .attr("height", function(d) { return headspace; })
          .attr("class", "bar_hidden")
          .on("mouseover", function(d,i) { $("svg.timeline text#text-bar-"+i).attr("class", "bar bar_highlight"); }) /* JQuery can't set classes on SVG */
          .on("mouseout", function(d,i) { $("svg.timeline text#text-bar-"+i).attr("class", "bar"); });
}

