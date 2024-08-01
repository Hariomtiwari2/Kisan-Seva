document.addEventListener('DOMContentLoaded', function () {
  var submenu = document.querySelector('.dropdown-submenu');
  submenu.addEventListener('mouseenter', function (e) {
    var subMenuToShow = this.querySelector('.dropdown-menu');
    subMenuToShow.classList.add('show');
  });
  submenu.addEventListener('mouseleave', function (e) {
    var subMenuToHide = this.querySelector('.dropdown-menu');
    subMenuToHide.classList.remove('show');
  });
});

// Function to display popup messages
function displayPopup(type) {
  var message = "";
  if (type === 'message') {
    message = "Kisan Seva is a groundbreaking website crafted by the passionate students of NIET Greater Noida, dedicated to addressing the pressing issues faced by farmers. Recognizing the invaluable contribution of farmers, the backbone of our society, Kisan Seva aims to uplift and empower this vital community. Through innovative solutions and unwavering dedication, we strive to ensure that farmers receive the recognition and support they truly deserve, safeguarding not only their livelihoods but also the sustenance of our entire society.";
  } else if (type === 'mission') {
    message = "Our platform, 'Kisan Seva,' leverages advanced machine learning to provide personalized crop recommendations based on soil quality, climate, and land size, optimizing profitability for farmers. We simplify access to legitimate loans by connecting farmers with reputable lenders for fair financing. Additionally, our online marketplace offers high-quality agricultural products at competitive prices, streamlining procurement and supporting effective farming operations. Through these services, we empower farmers, enhance agricultural practices, and promote sustainable growth in the farming industry.";
  }
  alert(message);  // Use alert to show the message
}

