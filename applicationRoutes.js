const express = require('express');
const applicationController = require('../controllers/applicationController');
const { protect, restrictTo } = require('../middlewares/authMiddleware');

const router = express.Router();

router.use(protect);

// Student routes
router.post('/apply', restrictTo('student'), applicationController.applyForJob);
router.get('/my-applications', restrictTo('student'), applicationController.getMyApplications);

// Company routes
router.get('/job/:jobId', restrictTo('company'), applicationController.getApplicationsForJob);
router.patch('/:id/status', restrictTo('company'), applicationController.updateApplicationStatus);

module.exports = router;
