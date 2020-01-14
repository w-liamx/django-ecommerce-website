//ES5
$.fn.stars = function(){
	return $(this).each(function(){
		var rating = $(this).data("rating");
		var fullStar = new Array(Math.floor(rating + 1)).join('<i class="fa fa-star"></i>');
		var halfStar = ((rating%1) !== 0) ? '<i class="fa fa-star-half-o"></i>': '';
		var noStar = new Array(Math.floor($(this).data("numStars") + 1 - rating)).join('<i class="fa fa-star-o empty"></i>');
		$(this).html(fullStar + halfStar + noStar);
	});
}

//ES6
$.fn.stars = function(){
	return $(this).each(function(){
		const rating = $(this).data("rating");
		const numStars = $(this).data("numStars");
		const fullStar = '<i class="fa fa-star"></i>'.repeat(Math.floor(rating));
		const halfStar = (rating%1 !== 0) ? '<i class="fa fa-star-half-o"></i>': '';
		const noStar = '<i class="fa fa-star-o empty"></i>'.repeat(Math.floor(numStars - rating));
		$(this).html(`${fullStar}${halfStar}${noStar}`);
	});
}