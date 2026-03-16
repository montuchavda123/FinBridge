const express = require('express');
const userController = require('../controllers/userController');
const { protect } = require('../middlewares/authMiddleware');

const router = express.Router();

router.use(protect); // All routes below require auth

router.patch('/profile', userController.updateProfile);

module.exports = router;
