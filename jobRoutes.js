const express = require('express');
const jobController = require('../controllers/jobController');
const { protect, restrictTo } = require('../middlewares/authMiddleware');

const router = express.Router();

// Allow reading jobs without authentication? Usually job boards allow this.
// But we'll enforce students to login.
router.use(protect);

router.route('/')
  .get(jobController.getAllJobs)
  .post(restrictTo('company'), jobController.createJob);

router.route('/:id')
  .get(jobController.getJob)
  .patch(restrictTo('company'), jobController.updateJob)
  .delete(restrictTo('company'), jobController.deleteJob);

module.exports = router;
