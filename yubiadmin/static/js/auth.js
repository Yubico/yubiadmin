$(document).ready(function() {
	$('#delete_btn').attr('disabled', 'disabled');

	$('#toggle_all').change(function() {
		$('tbody :checkbox').prop('checked', $(this).is(':checked'));
	});

	$(':checkbox').change(function() {
		if($('tbody :checkbox:checked').length > 0) {
			console.log('enable');
			$('#delete_btn').removeAttr('disabled');
		} else {
			console.log('disable');
			$('#delete_btn').attr('disabled', 'disabled');
		}
	});
});
