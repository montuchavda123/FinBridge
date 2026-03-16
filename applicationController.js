const Application = require('../models/Application');
const Job = require('../models/Job');
const catchAsync = require('../utils/catchAsync');
const AppError = require('../utils/appError');

exports.applyForJob = catchAsync(async (req, res, next) => {
  if (req.user.role !== 'student') {
    return next(new AppError('Only students can apply for jobs', 403));
  }

  const { jobId, resumeUsed } = req.body;

  if (!jobId || !resumeUsed) {
    return next(new AppError('Please provide jobId and resumeUsed', 400));
  }

  const job = await Job.findById(jobId);
  if (!job) {
    return next(new AppError('Job not found', 404));
  }

  const application = await Application.create({
    job: jobId,
    student: req.user._id,
    resumeUsed
  });

  res.status(201).json({
    status: 'success',
    data: {
      application
    }
  });
});

exports.getApplicationsForJob = catchAsync(async (req, res, next) => {
  const { jobId } = req.params;

  // Verify that the company owns this job
  const job = await Job.findById(jobId);
  if (!job) return next(new AppError('Job not found', 404));

  if (job.company.toString() !== req.user._id.toString()) {
    return next(new AppError('You are not authorized to view applications for this job', 403));
  }

  const applications = await Application.find({ job: jobId }).populate('student', 'name email');

  res.status(200).json({
    status: 'success',
    results: applications.length,
    data: {
      applications
    }
  });
});

exports.updateApplicationStatus = catchAsync(async (req, res, next) => {
  const { status } = req.body;
  const application = await Application.findById(req.params.id).populate('job');

  if (!application) {
    return next(new AppError('Application not found', 404));
  }

  if (application.job.company.toString() !== req.user._id.toString()) {
    return next(new AppError('You are not authorized to update this application', 403));
  }

  application.status = status;
  await application.save();

  res.status(200).json({
    status: 'success',
    data: {
      application
    }
  });
});

exports.getMyApplications = catchAsync(async (req, res, next) => {
  const applications = await Application.find({ student: req.user._id }).populate('job', 'title company');

  res.status(200).json({
    status: 'success',
    results: applications.length,
    data: {
      applications
    }
  });
});
