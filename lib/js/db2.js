

// Global Variables 
var ctx;
var slider, timeStart, timeEnd; // slider and selected values for time - reset on file load
var minTime, maxTime, minLat, maxLat, minLon, maxLon, minX, maxX, minY, maxY; // from all datasets loaded
var annimationInterval; // used to remember how long before updating graph in animation
var lastUpdate; // remembers last time graph was updated (so time delta can be calculated for annimation)
var editLabelDialog, label , labelID ; // to manage table list

// variables for DB2
var rawData = [], processedData = [], tableStats = []; 
var colors = ['#a50026','#d73027','#f46d43','#fdae61','#fee08b','#d9ef8b','#a6d96a','#66bd63','#1a9850','#006837'];
// var colors = ['#003f5c','#2f4b7c','#665191','#a05195','#d45087','#f95d6a','#ff7c43','#ffa600'];
var colorCounter = 0;

var progressBar = [];

const plugin = { // used to generate white background for screenshots.  
  id: 'customCanvasBackgroundColor',
  beforeDraw: (chart, args, options) => {
    const {ctx} = chart;
    ctx.save();
    ctx.globalCompositeOperation = 'destination-over';
    ctx.fillStyle = options.color || '#99ffff';
    ctx.fillRect(0, 0, chart.width, chart.height);
    ctx.restore();
  }
};

$(document).ready(function () {  
  /**
   * The following section function, will put any <a class="modal"...> into a dialog, that can be moved around
   * Currently used to provide help window.  
   * **/
  $('.modal').on('click', function(e){
      e.preventDefault();
      $('<div/>', {'class':'myDlgClass', 'id':'link-'+($(this).index()+1)})
      .load($(this).attr('href')).appendTo('body').dialog().dialog("option","title","Help");
  });
  $("#showNum").spinner({ // spinner to select number of tables to show
      step: 1,
      change: function( event, data ) {
        // console.log(event);
        sortTables($('#sortBy').val(), parseInt($('#showNum').val()));
      }
     });
  $("#showNum").width(30);
  $('#sortBy').selectmenu({
      change: function( event, data ) {
        sortTables(data.item.value, parseInt($('#showNum').val()));
      }
     });

  
  $("#rightcolumn").resizable({handles: 'e'});
  $("#leftcolumn").resizable({handles: 'e'});
  //$("#rightcolumn").draggable();
  //$("#leftcolumn").draggable();

  $( "#navbar" ).menu({position: {at: "left bottom"}});

  /** 
   * label, lableID editLabelDialog and form are all used as part of the ability to modify labels on
   * the boats, marks and lines
   * **/
  label = $( "#label" );    labelID = $( "#labelID" ); fullID = $("#fullID") ; // label and labelID are use for updating labels 
  accessRateMax = $("#accessRateMax"); accessRateAve = $("#accessRateAve");
  updateRateMax = $("#updateRateMax"); updateRateAve = $("#updateRateAve"); 
  editLabelDialog = $( "#dialog-editLabel" ).dialog({ //dialog that collects labels  
    autoOpen: false,
    height: 200,
    width: 350,
    modal: true,
    buttons: {
      "Update Label": updateLabel,
      Cancel: function() {
        editLabelDialog.dialog( "close" );
      }
    },
    close: function() {
      form[ 0 ].reset();
    }
  });
  form = editLabelDialog.find( "form" ).on( "submit", function( event ) {
    event.preventDefault();
    console.log(labelID.val() +" " + label.val())
    updateLabel();
  });

  // Slider at bottom of graph with start and finish times
  slider = $( "#slider" ).slider({
      range: true,
      min: 0,
      max: 500,
      values: [ 75, 300 ],
      slide: function( event, ui ) {
          //console.log( ui.values[ 0 ] + "  " + ui.values[ 1 ] );
          timeStart = ui.values[ 0 ];
          timeEnd = ui.values[ 1 ];
      updateTime();
    },
  });
  
  // Canvas for Plot, includes mousedown functions to add marks, and Lines
  ctx = $('#myChart');
      
  // Create chart variable
  var myChart = new Chart(ctx, {
      type: 'line',
      data: {}
  });
  
  document.querySelector("#csv").addEventListener('change',function () {
    var headerRegex = /^(\S+\s+){12,12}(\S+)$/;
    var rowRegex = /^(\S+\s+){8,8}(\S+)$/;
    var dateRegex = /[0-9]{4}(-[0-9]{2}){2}-([0-9]{2}.){2}[0-9]{2}/;
    var files = document.querySelector("#csv").files; // a collection of files, if the user selects more than one
    var counter = 0;
    var fileCount = files.length;
    
    Array.from(files).forEach(file => {
        // TBD perform validation on file type & size if required
        // loaderId+=1;
        progressBar[file.name] = $('<div><div  class="progress-label">Loading:'+file.name+'</div></div>').progressbar({
            value: false,
          });
        var reader = new FileReader();

        reader.addEventListener('loadstart', function() {
          // This event only useful, if Logging of file reading start is required
          
          $('#progressbars').append(progressBar[file.name]).append($(''));
        });

        reader.addEventListener('progress', function(e){
          if (e.lengthComputable) {
            var progress = ((e.loaded / e.total) * 50);
            // console.log(file.name+" "+e.loaded+" "+e.total);
            progressBar[file.name].progressbar('value', progress);
            // console.log(e.loaded+" "+e.total);
          }
        });
    
        reader.addEventListener('load', function(e) { // add listener for when file has finished loading
        // TO BE DONE: Validate csv format is good for this application
          result = e.target.result; // should contain a collection of rows from file
          //console.log(result);
          // const whiteSpaceParser = d3.dsvFormat(" ");
          //const data = whiteSpaceParser.parse(result);
          data = result.split(/\r?\n/); // Split into lines
          //console.log(data.length);
          dlength = data.length;
          for(var i=0; i<dlength; i++){
            //console.log(data[i])
            // Validate each row with a regex
            if (rowRegex.test(data[i].trim())){ //header row will be longer
              // need to convert data types and object
              row = data[i].trim().split(/\s+/g); //split on white space
              // Validate Date 
              if (dateRegex.test(row[4])){
                var rowObj = {id:row[3]+'.'+row[0]+'.'+row[1]+'.'+row[2],
                  timestamp:Date.parse((row[4].substring(0, 10) + 'T' + row[4].substring(10 + 1)).replaceAll('.',':')), 
                  accesses:+row[5], writes:+row[6], size:+row[7], prts:+row[8] }
                rawData.push(rowObj);
              } else {console.log("Bad date format: "+row[4]);}
            } else {
              if(!headerRegex.test(data[i])){ 
                console.log("Bad row format: "+ data[i])
              }
            }
            // console.log(file.name);
            // progressBar[file.name].progressbar('value', (1+i/dlength)*50)
            // if (row.length > 10)
          }
          // console.log(rawData);
          counter +=1;
          setTimeout(removeItem(file.name), 10000);
          console.log(counter+" of "+fileCount);
          if (counter >= fileCount){
            processRawData();
          }
          
        });
        reader.readAsText(file);
    });
  });     
 });

 function removeItem(item){
  progressBar[item].remove();
}
 function processRawData() {
  progressBar["processing"] = $('<div><div  class="progress-label">Processing data loaded ....</div></div>').progressbar({
    value: false,
  });
  $('#progressbars').append(progressBar["processing"]).append($(''));
  rawData = rawData.sort((a, b)=> { 
      if (a.id === b.id){
        return a.timestamp < b.timestamp ? -1 : 1
      } else {
        return a.id < b.id ? -1 : 1
      }
    })
  processedData.splice(0,processedData.length);
  tableStats.splice(0, tableStats.length);
  var previousRow = rawData[0];
  var firstTableRow = rawData[0];
  //var data = [];
  //data.push({});
  var aRateMax =0, uRateMax = 0; aRateSum=0; uRateSum=0; timeSum = 0; hasReorg = false;
  for(i=1; i<=rawData.length-1; i++){ //rawData.length-1
    currentRow = rawData[i];
    //if(currentRow.id === "EQ_POSSESSION.EQPMN001.EQ000310.EQ"){
        //console.log(aRateSum +" "+ uRateSum +" "+ timeSum+" "+arate+ " " + i);
        //console.log(currentRow);
    //}
    if(previousRow.id === currentRow.id){
      // console.log(currentRow.timestamp - previousRow.timestamp);
      // console.log(previousRow.timestamp<currentRow.timeStamp);
      if(currentRow.timestamp > previousRow.timestamp){
        var arate = 1000 * (currentRow.accesses-previousRow.accesses)/(currentRow.timestamp-previousRow.timestamp);
        if (arate>aRateMax) {aRateMax = arate;}
        var urate = 1000 * (currentRow.writes-previousRow.writes)/(currentRow.timestamp-previousRow.timestamp);
        if (urate>uRateMax) {uRateMax = urate;}
        // console.log(currentRow.timestamp - previousRow.timestamp);
        if(arate >= 0.0){
          processedData.push({id:currentRow.id,timestamp:previousRow.timestamp+100, 
            accessRate:arate, updateRate:urate});
          processedData.push({id:currentRow.id,timestamp:currentRow.timestamp, 
            accessRate:arate, updateRate:urate});
          aRateSum += currentRow.accesses-previousRow.accesses; 
          uRateSum += currentRow.writes-previousRow.writes; 
          timeSum += currentRow.timestamp-previousRow.timestamp;
        } else {hasReorg = true; }
      }
    } else {
      if(previousRow.timestamp>firstTableRow.timestamp && timeSum>0){
        var arate = 1000 * (aRateSum)/(timeSum);
        var urate = 1000 * (uRateSum)/(timeSum);
        // var arate = 1000 * (previousRow.accesses-firstTableRow.accesses)/(previousRow.timestamp-firstTableRow.timestamp);
        // var urate = 1000 * (previousRow.writes-firstTableRow.writes)/(previousRow.timestamp-firstTableRow.timestamp);

        var item = {id: previousRow.id ,label:previousRow.id.split('.')[0], accessRateMax: aRateMax, updateRateMax: uRateMax
          ,accessRateAve:arate, updateRateAve:urate, data:processedData.filter(function(el){ return el.id === previousRow.id})
          ,hidden: false, borderColor:colors[colorCounter], backgroundColor: colors[colorCounter]
          ,pointRadius:0,borderWidth: 1, hasReorg:hasReorg}
        tableStats.push(item);
        //if(item.id === "EQ_POSSESSION.EQPMN001.EQ000310.EQ"){
          //console.log(aRateSum +" "+ uRateSum +" "+ timeSum)
        //}
        aRateMax = 0; uRateMax = 0; firstTableRow=currentRow; colorCounter +=1;
        aRateSum =0; uRateSum = 0; timeSum = 0;
        if(colorCounter > colors.length-1){colorCounter = 0;}
        //data.splice(0,data.length);
      }
    }
    previousRow = currentRow;
  }

  sortTables('accessRateAve', 10)
  progressBar["processing"].progressbar('value', 100);
  setTimeout(removeItem("processing"), 2000);
}

function sortTables(method, factor){
  // console.log(method+" "+factor);
  tableStats = tableStats.sort((a,b)=> {return a[method] < b[method] ? 1 : -1 });
  // builtPlotData();
  //tableStats[0][method];
  colorCounter = 0;
  shownCounter = 1;
  // minTime = tableStats[0].data[0].timestamp;
  //maxTime = tableStats[0].data[0].timestamp;
  tableStats.forEach(function(item) {
    // if(item[method] > tableStats[0][method] / factor){
    if(shownCounter <= factor && !isNaN(item[method])){
      item.hidden = false;
      shownCounter +=1;
    } else {item.hidden = true;}
    item.borderColor = colors[colorCounter];
    item.backgroundColor = colors[colorCounter];
    // minTime = (minTime> d3.min())
    colorCounter +=1; colorCounter = (colorCounter > colors.length-1) ? 0 : colorCounter;
      
      // if(colorCounter > colors.length-1){colorCounter = 0;}
  })
  // console.log(tableStats);
  updateMaxMin()
 
  plotTable(ctx, Chart.getChart('myChart'), tableStats);
  // plotData();
  updateObjectList();
}

/** updateMaxMin updates all maximums and minimums
 * **/
function updateMaxMin (){
  if(tableStats.length > 1){
    minTime = d3.min(tableStats, function(ld){return d3.min(ld.data, function(d){return d.timestamp})});
    maxTime = d3.max(tableStats, function(ld){return d3.max(ld.data, function(d){return d.timestamp})});
    slider.slider("option", "min", minTime); slider.slider("option", "max", maxTime);
    slider.slider('values',0,minTime); // sets first handle (index 0) to 50
    slider.slider('values',1,maxTime);
  }
}

function downloadReport(){
  var element = document.getElementById('report');
  var opt = {
    margin:       1,
    filename:     'html2pdf_example.pdf',
    image:        { type: 'jpeg', quality: 0.98 },
    html2canvas:  { scale: 2 },
    pagebreak:    { mode: 'avoid-all', after: '#break' },
    jsPDF:        { unit: 'in', format: 'letter', orientation: 'portrait' }
  };
  // Choose the element that our invoice is rendered in.
  html2pdf().set(opt).from(element).save();
}

function generateReport(){
  $('#report').empty();
  tableStats.forEach(function(item) {
    //var smallDiv = '<div class="Card"><p></p></div>';
    if(!item.hidden){
      var smallDiv = '<div class="card" name="'+item.label+'"><h2>'+item.label+'</h2>';
      smallDiv += '<p>This tables has an average read rate (per second) of '+item.accessRateAve.toFixed()+' which represents a MIP usage of '+(item.accessRateAve/400).toFixed(1)+' to '+(item.accessRateAve/100).toFixed(1)+'MIPS for the entire period of the graph. </p>';
      smallDiv += '<p>This tables has an peak read rate (per second) of '+item.accessRateMax.toFixed()+' which represents a MIP usage of '+(item.accessRateMax/400).toFixed(1)+' to '+(item.accessRateMax/100).toFixed(1)+'MIPS for the entire period of the peak. </p>';
      if(item.hasReorg){smallDiv += '<p>This table has been reorg\'d at somepoint, which may impact results.  This is indicated on the graph by a sloped line (due to  missing data point when the reorg occured).</p>';}
      smallDiv += '</div>';
      var pagebreak = '<div id="break" name="break" class="break" style="break-before: always;"></div>';
      var canvas = document.createElement('canvas');
      $('#report').append(smallDiv).append(canvas).append(pagebreak);
      var ctxs = canvas.getContext("2d");
      var chart =  new Chart(ctxs, {
                                type: 'line',
                                data: {}
                            });
      plotTable(ctxs, chart, tableStats.filter(function(el){ return el.id === item.id}));
    }
  })
}

function plotTable(canvas, chart, toPlot){
  //console.log(item)
  // toPlot = tableStats.filter(function(el){ return el.id === itemId});
  // console.log(toPlot);
  const cfg = {
        type: 'line',
        data: { datasets: toPlot},
        options: {
          parsing: { xAxisKey: 'timestamp', yAxisKey: 'accessRate' },
          // events: ['onhover'] ,
          scales: {
              x: {
                  type: 'time',
                  time: {
                    //parser: 'MM/DD/YYYY HH:mm',
                    tooltipFormat: 'MM/dd/yyyy HH:mm',
                    minUnit: 'hour',
                    unitStepSize: 6,
                    displayFormats: {
                      'hour': 'HH:00',
                      'day': 'MM/dd/yyyy'
                    }
                  },
                  /**time: {
                      unit: 'hour',
                      unitStepSize: 6,
                  }, **/
                  ticks:{
                    enabled: true,
                    callback: function(val, index) {
                      // Hide every 2nd tick label
                      //console.log(val + " " + index + " "+ this.getLabelForValue(val));
                      return this.getLabelForValue(val);
                    },
                  },
                  title: {
                    display: true, 
                    text:"Time",
                  }
              },
              y: {
                title: {
                  display: true,
                  text: "Read rate (reads/second)",
                }
              }
          },
          animation: {
              duration: 0
          },
          hover: {
            mode: 'nearest',
            intersect: true
          },
          plugins: {
            //legend: {
              //display: false
            //},
            legend: {
              position: 'right',
              labels: {
                usePointStyle:true,
                pointStyle: 'line',
                filter: function(legendItem, data) {
                  let label = data.datasets[legendItem.datasetIndex].label || '';
                  if (data.datasets[legendItem.datasetIndex].hidden){
                    return false;
                  }
                  return label;
                }
              }
            },
            customCanvasBackgroundColor: {
              color: 'white',
            },
            tooltip:{
              enabled: true,
              mode: 'point',
              callbacks: {
                label: function(context){
                  let label = context.dataset.label || '';
                  if (label) {
                      label += ': ' + parseFloat(context.formattedValue).toFixed(0);
                      label += ' @ ' + context.label;
                  }
                  //console.log(context);
                  return label;
                }
              }
            },
            
          }  
        },
        plugins: [plugin],
      };
      // var myChart = Chart.getChart('myChart')
      chart.destroy();
      chart = new Chart(canvas, cfg);
}


/** updateTime()
 * Update graph filtering based  on start and end time values
 * **/
function updateTime()
{
  var myChart = Chart.getChart('myChart');
  myChart.options.scales.x.min = timeStart;
  myChart.options.scales.x.max = timeEnd;
  // If time difference between timeStart and timeEnd is small, add in 6 hour ticks
  myChart.update();
}
  
/** updateObjectList 
 *  Builds the list of objects, including options to delete, make invisible, etc
 * **/
function updateObjectList(){
  var loadedObjects = $('#loadedObjects')
  // var colors = ['#FF0000', '#00FF00', '#0000FF', '#808080']
  var colorString ='';
  loadedObjects.empty();
  $.each(tableStats, function(i)
  {
    colorString ='';
    colorString += '<option selected="selected" value="'+tableStats[i].borderColor+'" rgb="'+tableStats[i].borderColor+'" style="background-color:'+tableStats[i].borderColor+'"> </option>'
    $.each(colors, function(j){
       colorString += '<option value="'+colors[j]+'" rgb="'+colors[j]+'" style="background-color:'+colors[j]+'"> </option>'
    });
    if(tableStats[i].hidden){
      var vis_icon = '<span class="ui-icon ui-icon-check" onclick="showItem('+i+')"></span><span class="ui-icon ui-icon-blank"></span>'
    } else {
      var vis_icon = '<span class="ui-icon ui-icon-blank"></span><span class="ui-icon ui-icon-close" onclick="hideItem('+i+')"></span>'
    }
    loadedObjects.append(
      '<div>' 
      + vis_icon
      + '<select onchange="updateColor('+i+',this)" style="background-color:'+tableStats[i].borderColor+'">'+ colorString + '</select>'
      + '<span class="ui-icon ui-icon-trash" onclick="deleteItem('+i+')"></span>'
      + '<span class="ui-icon ui-icon-pencil" onclick="editLabelPopup('+i+')"></span>'
      + tableStats[i].label+'</div>'
    )
  });
}

/**
 * editLabelPopup - brings up the edit label dialog, and sets the values
 * updateLabel - then does the actual label updating, once users has entered the information
 * **/
function editLabelPopup(i){
  // console.log(i);
  labelID.val(i);
  label.val(tableStats[i].label);
  fullID.val(tableStats[i].id);
  accessRateMax.val(tableStats[i].accessRateMax);
  accessRateAve.val(tableStats[i].accessRateAve);
  updateRateMax.val(tableStats[i].updateRateMax);
  updateRateAve.val(tableStats[i].updateRateAve);
  editLabelDialog.dialog("open");
}
function updateLabel(){
  // console.log (labelID.val() + " " + label.val());
  tableStats[labelID.val()].label = label.val();
  editLabelDialog.dialog("close");
  updateObjectList();
}

/** 
 * deleteItem deletes and item from the list of plottable items
 * **/
function deleteItem(i){
  tableStats.splice(i,1);
  updateObjectList();
  Chart.getChart('myChart').update();
}

/** 
 * hideItem changes the visibility of an item.
 * **/
function hideItem(i){
  tableStats[i].hidden = true;
  updateObjectList();
  Chart.getChart('myChart').update();
}

/**
 * showItem changes the visitilbity of an item
 * **/
function showItem(i){
  tableStats[i].hidden = false;
  updateObjectList();
  Chart.getChart('myChart').update();
}

/**
 * Update Color, updates the color of the item, based on 
 * **/
function updateColor(i, color){
  console.log("updating color of "+i+" with "+color.value+" from "+tableStats[i].borderColor);
  tableStats[i].borderColor = color.value;
  updateObjectList();
  Chart.getChart('myChart').update();
}

/** 
 * Screen shot takes a PNG of the current chart and downloads it.  
 * TODO: add white background before downloading.
 * **/
function screenShot(){
  var a = document.createElement('a');
  //a.href = Chart.getChart('myChart').toBase64Image("image/png", 1.0);
  a.href = document.getElementById('myChart').toDataURL('image/png');
  a.download = 'screenshot.png';
  a.click();
}
