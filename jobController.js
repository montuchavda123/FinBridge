const Job = require('../models/Job');
const catchAsync = require('../utils/catchAsync');
const AppError = require('../utils/appError');

exports.createJob = catchAsync(async (req, res, next) => {
  if (req.user.role !== 'company') {
    return next(new AppError('Only companies can post jobs', 403));
  }

  const newJob = await Job.create({
    ...req.body,
    company: req.user._id
  });

  res.status(201).json({
    status: 'success',
    data: {
      job: newJob
    }
  });
});

exports.getAllJobs = catchAsync(async (req, res, next) => {
  // Filtering
  const queryObj = { ...req.query };
  const excludedFields = ['page', 'sort', 'limit', 'fields'];
  excludedFields.forEach(el => delete queryObj[el]);

  // Handle skills array filtering (e.g. skillsRequired[in]=React,Node)
  if (queryObj.skillsRequired && queryObj.skillsRequired.in) {
    queryObj.skillsRequired.$in = queryObj.skillsRequired.in.split(',');
    delete queryObj.skillsRequired.in;
  }

  let query = Job.find(queryObj);

  // Execute query
  const jobs = await query.populate('company', 'name email');

  res.status(200).json({
    status: 'success',
    results: jobs.length,
    data: {
      jobs
    }
  });
});

exports.getJob = catchAsync(async (req, res, next) => {
  const job = await Job.findById(req.params.id).populate('company', 'name email');

  if (!job) {
    return next(new AppError('No job found with that ID', 404));
  }

  res.status(200).json({
    status: 'success',
    data: {
      job
    }
  });
});

exports.updateJob = catchAsync(async (req, res, next) => {
  const job = await Job.findOneAndUpdate(
    { _id: req.params.id, company: req.user._id },
    req.body,
    { new: true, runValidators: true }
  );

  if (!job) {
    return next(new AppError('No job found with that ID or you are not authorized to update it', 404));
  }

  res.status(200).json({
    status: 'success',
    data: {
      job
    }
  });
});

exports.deleteJob = catchAsync(async (req, res, next) => {
  const job = await Job.findOneAndDelete({ _id: req.params.id, company: req.user._id });

  if (!job) {
    return next(new AppError('No job found with that ID or you are not authorized to delete it', 404));
  }

  res.status(204).json({
    status: 'success',
    data: null
  });
});
