// Standard category framework - matches backend categorization
const categories = [
  "E-commerce/Shopping",
  "Entertainment/Streaming",
  "Social Media/Networking",
  "Search Engine",
  "News/Media",
  "Education/Learning",
  "Finance/Banking",
  "Productivity/Tools",
  "Health/Medical",
  "Travel/Booking",
  "Government/Public Services",
  "Sports",
  "Gaming",
  "Food/Recipes",
  "Real Estate",
  "Jobs/Careers",
  "Technology/Software",
  "Forums/Communities",
  "General/Other"
];

const listContainer = document.getElementById("categoryList");
const status = document.getElementById("status");

// Render toggles
categories.forEach((cat) => {
  const div = document.createElement("div");
  div.className = "category-item";

  const label = document.createElement("label");
  label.textContent = cat;

  const toggle = document.createElement("label");
  toggle.className = "switch";
  const input = document.createElement("input");
  input.type = "checkbox";
  input.value = cat.toLowerCase(); // Store lowercase for matching

  const slider = document.createElement("span");
  slider.className = "slider";

  toggle.appendChild(input);
  toggle.appendChild(slider);
  div.appendChild(label);
  div.appendChild(toggle);
  listContainer.appendChild(div);
});

// Load saved categories
chrome.storage.sync.get(["blockedCategories"], (data) => {
  const blocked = data.blockedCategories || [];
  document
    .querySelectorAll(".switch input")
    .forEach((checkbox) => {
      checkbox.checked = blocked.includes(checkbox.value);
    });
});

// Handle toggle
document.addEventListener("change", (e) => {
  if (e.target.type === "checkbox") {
    chrome.storage.sync.get(["blockedCategories"], (data) => {
      let blocked = data.blockedCategories || [];

      if (e.target.checked) {
        if (!blocked.includes(e.target.value)) blocked.push(e.target.value);
      } else {
        blocked = blocked.filter((cat) => cat !== e.target.value);
      }

      chrome.storage.sync.set({ blockedCategories: blocked }, () => {
        status.textContent = "✅ Changes saved!";
        setTimeout(() => (status.textContent = ""), 2000);
      });
    });
  }
});