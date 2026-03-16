const Application = require('../models/Application');
const Job = require('../models/Job');
const catchAsync = require('../utils/catchAsync');
const AppError = require('../utils/appError');
const StudentProfile = require('../models/StudentProfile');

exports.getStudentDashboard = catchAsync(async (req, res, next) => {
  if (req.user.role !== 'student') {
    return next(new AppError('Unauthorized access', 403));
  }

  const applications = await Application.find({ student: req.user._id }).populate('job', 'title company status');
  const profile = await StudentProfile.findOne({ user: req.user._id });

  // Mock recommended jobs based on matching skills later. For now, just returning latest 5.
  const recommendedJobs = await Job.find({ status: 'Open' }).sort('-createdAt').limit(5);

  const appliedCount = applications.length;
  const interviewingCount = applications.filter(app => app.status === 'Interviewing').length;

  res.status(200).json({
    status: 'success',
    data: {
      stats: {
        appliedCount,
        interviewingCount,
        profileCompleted: profile ? profile.profileCompleted : false
      },
      recentApplications: applications.slice(0, 5),
      recommendedJobs
    }
  });
});

exports.getCompanyDashboard = catchAsync(async (req, res, next) => {
  if (req.user.role !== 'company') {
    return next(new AppError('Unauthorized access', 403));
  }

  const jobs = await Job.find({ company: req.user._id });
  const jobIds = jobs.map(job => job._id);

  const applications = await Application.find({ job: { $in: jobIds } });

  const totalJobs = jobs.length;
  const activeJobs = jobs.filter(job => job.status === 'Open').length;
  const totalApplicants = applications.length;
  const shortlistedCount = applications.filter(app => ['Shortlisted', 'Interviewing', 'Hired'].includes(app.status)).length;

  res.status(200).json({
    status: 'success',
    data: {
      stats: {
        totalJobs,
        activeJobs,
        totalApplicants,
        shortlistedCount
      },
      recentJobs: jobs.slice(0, 5)
    }
  });
});
