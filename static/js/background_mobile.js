document.addEventListener("DOMContentLoaded", function() {
  var granimInstance = new Granim({
    element: '#canvas-basic',
    name: 'basic-gradient',
    direction: 'left-right', // You can change this to 'top-bottom', 'radial', etc.
    opacity: [1, 1],
    isPausedWhenNotInView: true,
    stateTransitionSpeed: 1000,
    states: {
      "default-state": {
        gradients: [
          ['#ff7e5f', '#feb47b', '#fffc00'], // Gradient 1
          ['#6a11cb', '#2575fc', '#1a2a6c'], // Gradient 2
          ['#12c2e9', '#c471ed', '#f64f59'], // Gradient 3
          ['#333333', '#dd1818', '#234567'], // Gradient 4
          ['#ff9966', '#ff5e62', '#ff5e62'], // Gradient 5 - new
          ['#7F00FF', '#E100FF', '#E100FF'], // Gradient 6 - new
          ['#FAD961', '#F76B1C', '#F76B1C']  // Gradient 7 - new
        ],
        transitionSpeed: 10000
      }
    }
  });
});
