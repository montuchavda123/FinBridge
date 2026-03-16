const express = require('express');
const dashboardController = require('../controllers/dashboardController');
const { protect } = require('../middlewares/authMiddleware');

const router = express.Router();

router.use(protect);

router.get('/student', dashboardController.getStudentDashboard);
router.get('/company', dashboardController.getCompanyDashboard);

module.exports = router;
