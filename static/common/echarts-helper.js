function createPieChart(conf){
                var myChart = echarts.init(document.getElementById(conf.selector));
                var aLegend = [];
                var series = conf.data.series;
                for (var i = 0; i < series.length; i++) {
                     aLegend[i] = series[i].name;
                };
                // 填入数据
                myChart.setOption({
                    title : {
                        text: conf.data.title,
                        subtext: '',
                        x:'center'
                    },
                    legend: {
                        y: 'top',
                        data: aLegend
                    },
                    tooltip : {
                        trigger: 'item',
                        formatter: "{a} <br/>{b} : {c} ({d}%)"
                    },
                    calculable : true,
                    series: [{
                        // 根据名字对应到相应的系列
                        name:'访问来源',
                        type:'pie',
                        data: series
                    }]
                });
            }

function createBarChart(conf){
    var myChart = echarts.init(document.getElementById(conf.selector));
    var legendData = [];//存放变量的name
    for(var i = 0; i < conf.data.series.length; i++){
        legendData.push(conf.data.series[i].name);
    }
    myChart.setOption({
        legend: {
            y: 'top',
            data:legendData
        },
        tooltip : {
            trigger: 'axis'
        },
        calculable : true,
        yAxis : [
            {
                type : 'value',
                splitArea : {show : true}
            }
        ],
        xAxis : [
            {
                type : 'category',
                data : conf.data.xAxis
            }
        ],
        // xAxis : conf.data.xAxis,
        series : conf.data.series
    })
}
