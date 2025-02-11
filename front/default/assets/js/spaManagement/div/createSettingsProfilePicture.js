import { pushUrl } from '/static/default/assets/js/spaManagement/router.js';
import { modifyProfilPicture } from '/static/default/assets/js/action/userManagement.js';

function createSettingsProfilPicture() {

	try {
		const settingsProfilPictureDiv = document.getElementById("settings-profile-picture");

		// Back button
		const backButton = document.createElement("button");
		backButton.className = "arrow-back d-flex justify-content-start align-items-center";
		backButton.onclick = function() {
			pushUrl('/settings');
		};
		const backButtonImage = document.createElement("img");
		backButtonImage.src = "/static/default/assets/images/icons/arrow.svg";
		backButton.appendChild(backButtonImage);
		settingsProfilPictureDiv.appendChild(backButton);

		// Title and description
		const title = document.createElement("span");
		title.className = "title-2 greened";
		title.textContent = "Modify profile picture";
		settingsProfilPictureDiv.appendChild(title);

		const description = document.createElement("span");
		description.className = "body-text settings-text";
		description.textContent = "So we can see your lovely smile.";
		settingsProfilPictureDiv.appendChild(description);

		// Block to wrap items
		const blockDiv = document.createElement('div')
		blockDiv.classList.add('block-scroll')
		blockDiv.style.setProperty('--top', '5%')

		// Custom file input
		const customFileInput = document.createElement("label");
		customFileInput.className = "custom-file-input";
			
		const fileImage = document.createElement("img");
		fileImage.src = "/static/default/assets/images/icons/upload.svg";
			
		const fileInput = document.createElement("input");
		fileInput.type = "file";
		fileInput.id = "settings-profile-picture-input";
		fileInput.accept = "image/*";

		const fileSpan = document.createElement('span');
		fileSpan.id = 'custom-file-input-span'
		fileSpan.textContent = "Choose a file";
		
		customFileInput.appendChild(fileSpan);
		customFileInput.appendChild(fileImage);
		customFileInput.appendChild(fileInput);

		// Button
		const button = document.createElement("button");
		button.className = "btn btn-light bordered-button-expanded";
		button.style.setProperty("--main_color", "#DADADA");
		button.onclick = modifyProfilPicture;
		const buttonSpan = document.createElement("span");
		buttonSpan.className = "btn-title";
		buttonSpan.textContent = "Change my profile picture";
		button.appendChild(buttonSpan);

		blockDiv.appendChild(customFileInput)
		blockDiv.appendChild(button)
		settingsProfilPictureDiv.appendChild(blockDiv);	

	} catch (error) {
		console.error("Error in createSettingsProfilPicture: ", error);
		throw error;
	}
}

export { createSettingsProfilPicture };
