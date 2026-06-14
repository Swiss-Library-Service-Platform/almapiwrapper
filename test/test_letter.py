import glob
import os
import unittest

from almapiwrapper.config import Letter


class TestLetter(unittest.TestCase):
	def test_get_letter(self):
		# Test d'integration minimal: verifier qu'une lettre peut etre recuperee
		letter = Letter('FulUserBorrowingActivityLetter', 'NZ', 'S')
		self.assertIsNotNone(letter.data)
		self.assertFalse(letter.error)

	def test_update_letter_enabled(self):
		# Modifie uniquement le flag enabled puis restaure la valeur initiale
		letter = Letter('FulUserBorrowingActivityLetter', 'NZ', 'S')
		self.assertIsNotNone(letter.data)
		self.assertFalse(letter.error)

		initial_enabled = letter.enabled
		letter.enabled = not initial_enabled
		letter.update()
		self.assertFalse(letter.error)

		updated = Letter('FulUserBorrowingActivityLetter', 'NZ', 'S')
		self.assertEqual(updated.enabled, (not initial_enabled))

		updated.enabled = initial_enabled
		updated.update()
		self.assertFalse(updated.error)

	def test_save_letter_and_cleanup(self):
		letter = Letter('FulUserBorrowingActivityLetter', 'NZ', 'S')
		self.assertIsNotNone(letter.data)
		self.assertFalse(letter.error)

		# Sauvegarde locale avec versioning (_01, _02, ...)
		letter.save()

		created_files = glob.glob('records/letters/NZ_FulUserBorrowingActivityLetter_*.xml')
		self.assertGreater(len(created_files), 0, 'No files were created')

		# Nettoyage: suppression des fichiers de test puis dossier s il est vide
		for filepath in created_files:
			if os.path.isfile(filepath):
				os.remove(filepath)

		letters_dir = os.path.join('records', 'letters')
		if os.path.isdir(letters_dir) and len(os.listdir(letters_dir)) == 0:
			os.rmdir(letters_dir)


if __name__ == '__main__':
	unittest.main()

