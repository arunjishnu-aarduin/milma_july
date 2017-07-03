function getPackages(sel)
{    var x = document.getElementById("stockOutpackage");
		x.options.length=0;
		var option = document.createElement("option");
		option.setAttribute("value", "arun");
		option.text = "arun";
		x.add(option);
		$.ajax(
		{	url: '{% url "prediction:dynamicpackage" %}',
			data: {'product': sel.value},
			dataType: 'json',
			success: function (data) {
					if (data.packages) {
						x.options.length=0;
						for (var i = 0; i < data.size; i++) {
							var option = document.createElement("option");
							option.setAttribute("value",data.packages[i].packageId);
							option.text = data.packages[i].packageName;
							//option.text = data.size
							x.add(option);
						}
					}

			}
		});
}
