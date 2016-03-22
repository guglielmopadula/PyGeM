"""
Utilities for performing Free Form Deformation (FFD)
"""
import numpy as np
from scipy import special
import pygem.affine_trans as at


class FFD(object):
	"""
	DOCS
    """

	def __init__(self, ffd_parameters, original_mesh_points):
		self.parameters = ffd_parameters
		self.original_mesh_points = original_mesh_points


	def perform(self):
		"""
		DOCS
		"""
		(n_rows_mesh, n_cols_mesh) = self.original_mesh_points.shape

		# translation and then affine transformation
		translation = self.parameters.origin_box

		fisical_frame = np.array([self.parameters.position_vertex_1 - translation, \
			  self.parameters.position_vertex_2 - translation, \
			  self.parameters.position_vertex_3 - translation, \
			  [0, 0, 0]])
		reference_frame = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1], [0, 0, 0]])

		transformation = at.affine_points_fit(fisical_frame, reference_frame)
		inverse_transformation = at.affine_points_fit(reference_frame, fisical_frame)

		# initialization
		(dim_n_mu, dim_m_mu, dim_t_mu) = self.parameters.array_mu_x.shape
		bernstein_x = np.zeros((n_rows_mesh, dim_n_mu))
		bernstein_y = np.zeros((n_rows_mesh, dim_m_mu))
		bernstein_z = np.zeros((n_rows_mesh, dim_t_mu))
		shift_mesh_points = np.zeros((n_rows_mesh, n_cols_mesh))

		reference_frame_mesh_points = self._transform_points(self.original_mesh_points - translation, \
															 transformation)

		for i in range(0, dim_n_mu):
			aux1 = np.power((1-reference_frame_mesh_points[:, 0]), dim_n_mu-1-i)
			aux2 = np.power(reference_frame_mesh_points[:, 0], i)
			bernstein_x[:, i] = special.binom(dim_n_mu-1, i) * np.multiply(aux1, aux2)

		for i in range(0, dim_m_mu):
			aux1 = np.power((1-reference_frame_mesh_points[:, 1]), dim_m_mu-1-i)
			aux2 = np.power(reference_frame_mesh_points[:, 1], i)
			bernstein_y[:, i] = special.binom(dim_m_mu-1, i) * np.multiply(aux1, aux2)

		for i in range(0, dim_t_mu):
			aux1 = np.power((1-reference_frame_mesh_points[:, 2]), dim_t_mu-1-i)
			aux2 = np.power(reference_frame_mesh_points[:, 2], i)
			bernstein_z[:, i] = special.binom(dim_t_mu-1, i) * np.multiply(aux1, aux2)

		for i in range(0, dim_n_mu):
			for j in range(0, dim_m_mu):
				for k in range(0, dim_t_mu):
					aux = np.multiply(bernstein_x[:, i], np.multiply(bernstein_y[:, j], bernstein_z[:, k]))
					aux_x = aux * self.parameters.array_mu_x[i, j, k]
					aux_y = aux * self.parameters.array_mu_y[i, j, k]
					aux_z = aux * self.parameters.array_mu_z[i, j, k]
					shift_mesh_points[:, 0] += aux_x
					shift_mesh_points[:, 1] += aux_y
					shift_mesh_points[:, 2] += aux_z

		# Splitting points inside and outside the lattice: TODO not very efficient
		for i in range(0, n_rows_mesh):
			if (reference_frame_mesh_points[i, 0] < 0) or (reference_frame_mesh_points[i, 1] < 0) \
			or (reference_frame_mesh_points[i, 2] < 0) or (reference_frame_mesh_points[i, 0] > 1) \
			or (reference_frame_mesh_points[i, 1] > 1) or (reference_frame_mesh_points[i, 2] > 1):
				shift_mesh_points[i, :] = 0

		return self._transform_points(shift_mesh_points + reference_frame_mesh_points, \
									  inverse_transformation) + translation


	def _transform_points(self, original_points, transformation):
		"""
		DOCS
		"""
		n_rows_mesh, n_cols_mesh = original_points.shape
		modified_points = np.zeros((n_rows_mesh, n_cols_mesh))

		for i in range(0, n_rows_mesh):
			single_point = original_points[i]
			modified_points[i, :] = transformation(single_point)

		return modified_points