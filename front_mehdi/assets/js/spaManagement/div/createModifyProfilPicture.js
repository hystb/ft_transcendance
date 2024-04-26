import { changeScene } from '../scene.js';
import { modifyProfilPicture } from '../../action/userManagement.js';

async function createModifyProfilPicture() {

	try {
		const modifyProfilPictureDiv = document.getElementById("modify-profil-picture");

		// Back button
		const backButton = document.createElement("button");
		backButton.className = "arrow-back d-flex justify-content-start align-items-center";
		backButton.onclick = function() {
			changeScene('settings');
		};
		const backButtonImage = document.createElement("img");
		backButtonImage.src = "assets/images/icons/arrow.svg";
		backButton.appendChild(backButtonImage);
		modifyProfilPictureDiv.appendChild(backButton);

		// Title and description
		const title = document.createElement("span");
		title.className = "title-2 greened";
		title.textContent = "Modify profil picture";
		modifyProfilPictureDiv.appendChild(title);

		const description = document.createElement("span");
		description.className = "body-text settings-text";
		description.textContent = "So we can see your lovely smile.";
		modifyProfilPictureDiv.appendChild(description);

		// Custom file input
		const customFileInput = document.createElement("div");
		customFileInput.className = "custom-file-input";
		const fileImage = document.createElement("img");
		fileImage.src = "assets/images/icons/upload.svg";
		customFileInput.appendChild(fileImage);
		const fileLabel = document.createElement("label");
		fileLabel.htmlFor = "settings-profil-picture";
		fileLabel.textContent = "Choose a file";
		customFileInput.appendChild(fileLabel);
		const fileInput = document.createElement("input");
		fileInput.type = "file";
		fileInput.id = "settings-profil-picture";
		fileInput.accept = "image/*";
		customFileInput.appendChild(fileInput);
		modifyProfilPictureDiv.appendChild(customFileInput);

		// Button
		const button = document.createElement("button");
		button.className = "btn btn-light bordered-button-expanded";
		button.style.setProperty("--main_color", "#DADADA");
		button.onclick = modifyProfilPicture;
		const buttonSpan = document.createElement("span");
		buttonSpan.className = "btn-title";
		buttonSpan.textContent = "Change my profil picture";
		button.appendChild(buttonSpan);
		modifyProfilPictureDiv.appendChild(button);	

	} catch (error) {
		console.error("Error in createModifyProfilPicture: ", error);
		throw error;
	}
}

export { createModifyProfilPicture };
